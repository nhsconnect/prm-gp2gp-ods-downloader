import boto3
from moto import mock_s3

from prmods.io.s3 import S3DataManager
from tests.builders.file import build_gzip_csv
from tests.unit.io.s3 import MOTO_MOCK_REGION


@mock_s3
def test_returns_csv_row_as_dictionary():
    conn = boto3.resource("s3", region_name=MOTO_MOCK_REGION)
    bucket = conn.create_bucket(Bucket="test_bucket")
    s3_object = bucket.Object("test_object.csv.gz")
    s3_object.put(
        Body=build_gzip_csv(
            header=["header1", "header2"],
            rows=[["row1-col1", "row1-col2"], ["row2-col1", "row2-col2"]],
        )
    )

    s3_manager = S3DataManager(conn)

    expected = [
        {"header1": "row1-col1", "header2": "row1-col2"},
        {"header1": "row2-col1", "header2": "row2-col2"},
    ]

    actual = s3_manager.read_gzip_csv("s3://test_bucket/test_object.csv.gz")

    assert list(actual) == expected
