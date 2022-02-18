import json
import logging
from io import BytesIO
from os import environ
from threading import Thread

import boto3
from botocore.config import Config
from moto.server import DomainDispatcherApplication, create_backend_app
from werkzeug import Request, Response
from werkzeug.serving import make_server

from prmods.pipeline.main import main
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
S3_OUTPUT_ODS_METADATA_BUCKET_NAME = "prm-gp2gp-ods-data"

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
    b'{"Name": "Test GP 2 Duplicate", "OrgId": "B12345"}, '
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
    target_org_id_lookup = {
        "12A": MOCK_CCG_PRACTICES_RESPONSE_CONTENT_1,
        "13B": MOCK_CCG_PRACTICES_RESPONSE_CONTENT_2,
        "14C": MOCK_CCG_PRACTICES_RESPONSE_CONTENT_3,
    }
    primary_role_lookup = {
        "RO177": MOCK_PRACTICE_RESPONSE_CONTENT,
        "RO98": MOCK_CCG_RESPONSE_CONTENT,
    }

    if primary_role:
        return primary_role_lookup[primary_role]
    else:
        return target_org_id_lookup[target_org_id]


def _build_fake_s3(host, port):
    app = DomainDispatcherApplication(create_backend_app, "s3")
    server = make_server(host, port, app)
    return ThreadedServer(server)


def _build_fake_ods(host, port):
    server = make_server(host, port, fake_ods_application)
    return ThreadedServer(server)


def _disable_werkzeug_logging():
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)


def _read_s3_json_file(bucket, key):
    f = BytesIO()
    bucket.download_fileobj(key, f)
    f.seek(0)
    return json.loads(f.read().decode("utf-8"))


def _read_s3_metadata(bucket, key):
    return bucket.Object(key).get()["Metadata"]


def _build_fake_s3_bucket(bucket_name: str, s3):
    s3_fake_bucket = s3.Bucket(bucket_name)
    s3_fake_bucket.create()
    return s3_fake_bucket


def _setup():
    s3_client = boto3.resource(
        "s3",
        endpoint_url=FAKE_S3_URL,
        aws_access_key_id=FAKE_S3_ACCESS_KEY,
        aws_secret_access_key=FAKE_S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=FAKE_S3_REGION,
    )

    environ["AWS_ACCESS_KEY_ID"] = "testing"
    environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    environ["AWS_DEFAULT_REGION"] = "us-west-1"

    environ["DATE_ANCHOR"] = "2020-01-30T18:44:49Z"
    environ["OUTPUT_BUCKET"] = S3_OUTPUT_ODS_METADATA_BUCKET_NAME
    environ["MAPPING_BUCKET"] = "prm-gp2gp-ods-data"
    environ["S3_ENDPOINT_URL"] = FAKE_S3_URL
    environ["SEARCH_URL"] = FAKE_ODS_PORTAL_URL
    environ["BUILD_TAG"] = "61ad1e1c"

    fake_s3 = _build_fake_s3(FAKE_S3_HOST, FAKE_S3_PORT)
    fake_ods = _build_fake_ods(FAKE_ODS_HOST, FAKE_ODS_PORT)
    return fake_s3, fake_ods, s3_client


def test_with_s3():
    _disable_werkzeug_logging()

    fake_s3, fake_ods, s3_client = _setup()
    fake_s3.start()
    fake_ods.start()

    year = 2020
    month = 1

    output_bucket = _build_fake_s3_bucket(S3_OUTPUT_ODS_METADATA_BUCKET_NAME, s3_client)
    output_bucket.upload_fileobj(INPUT_ASID_CSV, f"{year}/{month}/asidLookup.csv.gz")

    try:
        main()

        output_path = f"v3/{year}/{month}/organisationMetadata.json"
        actual = _read_s3_json_file(output_bucket, output_path)

        assert actual["year"] == year
        assert actual["month"] == month
        assert actual["practices"] == EXPECTED_PRACTICES
        assert actual["ccgs"] == EXPECTED_CCGS

        expected_metadata = {"date-anchor": "2020-01-30T18:44:49+00:00", "build-tag": "61ad1e1c"}
        actual_s3_metadata = _read_s3_metadata(output_bucket, output_path)

        assert actual_s3_metadata == expected_metadata

    finally:
        fake_ods.stop()
        fake_s3.stop()
        environ.clear()
