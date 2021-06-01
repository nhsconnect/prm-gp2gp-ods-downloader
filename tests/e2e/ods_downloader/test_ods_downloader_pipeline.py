import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import parse_qs

import boto3

from os import environ
from threading import Thread
from botocore.config import Config
from botocore.exceptions import ClientError
from moto.server import DomainDispatcherApplication, create_backend_app
from werkzeug.serving import make_server

from prmods.pipeline.ods_downloader.config import OdsPortalConfig
from prmods.pipeline.ods_downloader.main import main

from src.prmods.pipeline.ods_downloader.main import VERSION
from tests.builders.file import build_gzip_csv

FAKE_ODS_HOST = "127.0.0.1"
FAKE_ODS_PORT = 9000
FAKE_ODS_PORTAL_URL = f"http://{FAKE_ODS_HOST}:{FAKE_ODS_PORT}"

FAKE_S3_HOST = "127.0.0.1"
FAKE_S3_PORT = 8887
FAKE_S3_URL = f"http://{FAKE_S3_HOST}:{FAKE_S3_PORT}"
FAKE_S3_ACCESS_KEY = "testing"
FAKE_S3_SECRET_KEY = "testing"
FAKE_S3_REGION = "us-west-1"

INPUT_ROWS = [
    ["000011357014", "A12345", "Test GP", "Supplier", "system", "Practice", "HT87 1PQ"],
    ["000022357014", "B12345", "Test GP 2", "Supplier", "System", "Practice", "HY87 1PQ"],
    ["000033357014", "C12345", "Test GP 3", "Supplier", "System", "Practice", "HP87 1PQ"],
    ["123433357014", "C12345", "Test GP 3", "Supplier", "Other System", "Practice", "HP87 1PQ"],
    ["000044357014", "D12345", "Test GP 4", "Supplier", "System", "Practice", "HQ87 1PQ"],
    ["000055357014", "E12345", "Test GP 5", "Supplier", "System", "Practice", "HZ87 1PQ"],
]

INPUT_ASID_CSV = BytesIO(
    build_gzip_csv(
        header=["ASID", "NACS", "OrgName", "MName", "PName", "OrgType", "PostCode"], rows=INPUT_ROWS
    )
)

MOCK_PRACTICE_RESPONSE_CONTENT = (
    b'{"Organisations": [{"Name": "Test GP", "OrgId": "A12345"}, '
    b'{"Name": "Test GP 2", "OrgId": "B12345"}, '
    b'{"Name": "Test GP 3", "OrgId": "C12345"}]}'
)
MOCK_CCG_RESPONSE_CONTENT = (
    b'{"Organisations": [{"Name": "Test CCG", "OrgId": "12A"}, '
    b'{"Name": "Test CCG 2", "OrgId": "13B"}, '
    b'{"Name": "Test CCG 3", "OrgId": "14C"}]}'
)

EXPECTED_PRACTICES = [
    {"ods_code": "A12345", "name": "Test GP", "asids": ["000011357014"]},
    {"ods_code": "B12345", "name": "Test GP 2", "asids": ["000022357014"]},
    {"ods_code": "C12345", "name": "Test GP 3", "asids": ["000033357014", "123433357014"]},
]

EXPECTED_CCGS = [
    {"ods_code": "12A", "name": "Test CCG"},
    {"ods_code": "13B", "name": "Test CCG 2"},
    {"ods_code": "14C", "name": "Test CCG 3"},
]


class ThreadedServer:
    def __init__(self, server):
        self._server = server
        self._thread = Thread(target=server.serve_forever)

    def start(self):
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._thread.join()


class MockOdsRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_params = parse_qs(self.path[2:])
        primary_role = parsed_params["PrimaryRoleId"][0]

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(
            MOCK_PRACTICE_RESPONSE_CONTENT if primary_role == "RO177" else MOCK_CCG_RESPONSE_CONTENT
        )


def _build_fake_s3(host, port):
    app = DomainDispatcherApplication(create_backend_app, "s3")
    server = make_server(host, port, app)
    return ThreadedServer(server)


def _build_fake_ods(host, port):
    server = make_server(host, port, request_handler=MockOdsRequestHandler)
    return ThreadedServer(server)


def _read_s3_json_file(bucket, key):
    f = BytesIO()
    bucket.download_fileobj(key, f)
    f.seek(0)
    return json.loads(f.read().decode("utf-8"))


def test_with_s3():
    fake_s3 = _build_fake_s3(FAKE_S3_HOST, FAKE_S3_PORT)
    fake_s3.start()

    fake_ods = _build_fake_ods(FAKE_ODS_HOST, FAKE_ODS_PORT)
    fake_ods.start()

    s3 = boto3.resource(
        "s3",
        endpoint_url=FAKE_S3_URL,
        aws_access_key_id=FAKE_S3_ACCESS_KEY,
        aws_secret_access_key=FAKE_S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=FAKE_S3_REGION,
    )

    output_bucket_name = "prm-gp2gp-ods-data"
    output_bucket = s3.Bucket(output_bucket_name)
    output_bucket.create()

    month = datetime.utcnow().month
    year = datetime.utcnow().year

    output_bucket.upload_fileobj(INPUT_ASID_CSV, f"{year}/{month}/asidLookup.csv.gz")

    environ["AWS_ACCESS_KEY_ID"] = "testing"
    environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    environ["AWS_DEFAULT_REGION"] = "us-west-1"

    main(
        OdsPortalConfig(
            output_bucket="prm-gp2gp-ods-data",
            mapping_bucket="prm-gp2gp-ods-data",
            s3_endpoint_url=FAKE_S3_URL,
            search_url=FAKE_ODS_PORTAL_URL,
        )
    )

    actual = _read_s3_json_file(
        output_bucket, f"{VERSION}/{year}/{month}/organisationMetadata.json"
    )

    try:
        assert actual["practices"] == EXPECTED_PRACTICES
        assert actual["ccgs"] == EXPECTED_CCGS
    finally:
        output_bucket.objects.all().delete()
        output_bucket.delete()
        fake_ods.stop()
        fake_s3.stop()


def test_error_when_unable_to_locate_asid_look_up_file():
    fake_s3 = _build_fake_s3(FAKE_S3_HOST, FAKE_S3_PORT)
    fake_s3.start()

    fake_ods = _build_fake_ods(FAKE_ODS_HOST, FAKE_ODS_PORT)
    fake_ods.start()

    s3 = boto3.resource(
        "s3",
        endpoint_url=FAKE_S3_URL,
        aws_access_key_id=FAKE_S3_ACCESS_KEY,
        aws_secret_access_key=FAKE_S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=FAKE_S3_REGION,
    )

    output_bucket_name = "prm-gp2gp-ods-data"
    output_bucket = s3.Bucket(output_bucket_name)
    output_bucket.create()

    try:
        main(
            OdsPortalConfig(
                output_bucket="prm-gp2gp-ods-data",
                mapping_bucket="prm-gp2gp-ods-data",
                s3_endpoint_url=FAKE_S3_URL,
                search_url=FAKE_ODS_PORTAL_URL,
            )
        )
    except ClientError as ex:
        assert ex.__str__().__contains__("NoSuchKey")

    output_bucket.objects.all().delete()
    output_bucket.delete()
    fake_ods.stop()
    fake_s3.stop()
