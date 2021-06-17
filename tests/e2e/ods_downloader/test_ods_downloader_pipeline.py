import json
from io import BytesIO

import boto3

from os import environ
from threading import Thread
from botocore.config import Config
from moto.server import DomainDispatcherApplication, create_backend_app
from werkzeug import Response, Request
from werkzeug.serving import make_server

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
MOCK_CCG_PRACTICES_RESPONSE_CONTENT_1 = (
    b'{"Organisations": [{"Name": "Test GP", "OrgId": "A12345"}]}'
)
MOCK_CCG_PRACTICES_RESPONSE_CONTENT_2 = b'{"Organisations": []} '
MOCK_CCG_PRACTICES_RESPONSE_CONTENT_3 = (
    b'{"Organisations": [{"Name": "Test GP 2", "OrgId": "B12345"}, '
    b'{"Name": "Test GP 3", "OrgId": "C12345"}]}'
)

EXPECTED_PRACTICES = [
    {"ods_code": "A12345", "name": "Test GP", "asids": ["000011357014"]},
    {"ods_code": "B12345", "name": "Test GP 2", "asids": ["000022357014"]},
    {"ods_code": "C12345", "name": "Test GP 3", "asids": ["000033357014", "123433357014"]},
]

EXPECTED_CCGS = [
    {"ods_code": "12A", "name": "Test CCG", "practices": ["A12345"]},
    {"ods_code": "13B", "name": "Test CCG 2", "practices": []},
    {"ods_code": "14C", "name": "Test CCG 3", "practices": ["B12345", "C12345"]},
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


@Request.application
def fake_ods_application(request):
    primary_role = request.args.get("PrimaryRoleId")
    target_org_id = request.args.get("TargetOrgId")

    return Response(
        _get_fake_response(primary_role, target_org_id),
        mimetype="application/json",
    )


def _get_fake_response(primary_role, target_org_id):
    if primary_role == "RO177":
        return MOCK_PRACTICE_RESPONSE_CONTENT
    elif target_org_id == "12A":
        return MOCK_CCG_PRACTICES_RESPONSE_CONTENT_1
    elif target_org_id == "13B":
        return MOCK_CCG_PRACTICES_RESPONSE_CONTENT_2
    elif target_org_id == "14C":
        return MOCK_CCG_PRACTICES_RESPONSE_CONTENT_3
    else:
        return MOCK_CCG_RESPONSE_CONTENT


def _build_fake_s3(host, port):
    app = DomainDispatcherApplication(create_backend_app, "s3")
    server = make_server(host, port, app)
    return ThreadedServer(server)


def _build_fake_ods(host, port):
    server = make_server(host, port, fake_ods_application)
    return ThreadedServer(server)


def _read_s3_json_file(bucket, key):
    f = BytesIO()
    bucket.download_fileobj(key, f)
    f.seek(0)
    return json.loads(f.read().decode("utf-8"))


def test_with_s3():
    s3 = boto3.resource(
        "s3",
        endpoint_url=FAKE_S3_URL,
        aws_access_key_id=FAKE_S3_ACCESS_KEY,
        aws_secret_access_key=FAKE_S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=FAKE_S3_REGION,
    )

    output_bucket_name = "prm-gp2gp-ods-data"

    environ["AWS_ACCESS_KEY_ID"] = "testing"
    environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    environ["AWS_DEFAULT_REGION"] = "us-west-1"

    environ["DATE_ANCHOR"] = "2020-01-30T18:44:49Z"
    environ["OUTPUT_BUCKET"] = output_bucket_name
    environ["MAPPING_BUCKET"] = "prm-gp2gp-ods-data"
    environ["S3_ENDPOINT_URL"] = FAKE_S3_URL
    environ["SEARCH_URL"] = FAKE_ODS_PORTAL_URL

    year = 2020
    month = 1

    fake_s3 = _build_fake_s3(FAKE_S3_HOST, FAKE_S3_PORT)
    fake_ods = _build_fake_ods(FAKE_ODS_HOST, FAKE_ODS_PORT)

    try:
        fake_s3.start()
        fake_ods.start()

        output_bucket = s3.Bucket(output_bucket_name)
        output_bucket.create()
        output_bucket.upload_fileobj(INPUT_ASID_CSV, f"{year}/{month}/asidLookup.csv.gz")

        main()

        actual = _read_s3_json_file(
            output_bucket, f"{VERSION}/{year}/{month}/organisationMetadata.json"
        )
        assert actual["practices"] == EXPECTED_PRACTICES
        assert actual["ccgs"] == EXPECTED_CCGS
    finally:
        fake_ods.stop()
        fake_s3.stop()
