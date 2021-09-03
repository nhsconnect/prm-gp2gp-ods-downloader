from datetime import datetime
from unittest import mock

import boto3
from moto import mock_s3

from prmods.utils.io.s3 import S3DataManager, logger
from tests.unit.utils.io.s3 import MOTO_MOCK_REGION


@mock_s3
def test_writes_dictionary():
    conn = boto3.resource("s3", region_name=MOTO_MOCK_REGION)
    bucket = conn.create_bucket(Bucket="test_bucket")
    s3 = S3DataManager(conn)
    data = {"fruit": "mango"}

    expected = b'{"fruit": "mango"}'

    s3.write_json("s3://test_bucket/test_object.json", data)

    actual = bucket.Object("test_object.json").get()["Body"].read()

    assert actual == expected


@mock_s3
def test_writes_dictionary_with_timestamp():
    conn = boto3.resource("s3", region_name=MOTO_MOCK_REGION)
    bucket = conn.create_bucket(Bucket="test_bucket")
    s3 = S3DataManager(conn)
    data = {"timestamp": datetime(2020, 7, 23)}

    expected = b'{"timestamp": "2020-07-23T00:00:00"}'

    s3.write_json("s3://test_bucket/test_object.json", data)

    actual = bucket.Object("test_object.json").get()["Body"].read()

    assert actual == expected


@mock_s3
def test_writes_correct_content_type():
    conn = boto3.resource("s3", region_name=MOTO_MOCK_REGION)
    bucket = conn.create_bucket(Bucket="test_bucket")
    data = {"fruit": "mango"}
    s3_manager = S3DataManager(conn)

    expected = "application/json"

    s3_manager.write_json("s3://test_bucket/test_object.json", data)

    actual = bucket.Object("test_object.json").get()["ContentType"]

    assert actual == expected


@mock_s3
def test_will_log_writing_file_events():
    conn = boto3.resource("s3", region_name=MOTO_MOCK_REGION)
    bucket_name = "test_bucket"
    conn.create_bucket(Bucket=bucket_name)
    data = {"fruit": "mango"}

    s3_manager = S3DataManager(conn)
    s3_file_path = f"s3://{bucket_name}/test_object.json"

    with mock.patch.object(logger, "info") as mock_log_info:
        s3_manager.write_json(s3_file_path, data)
        mock_log_info.assert_has_calls(
            [
                mock.call(
                    f"Attempting to upload: {s3_file_path}",
                    extra={"event": "ATTEMPTING_UPLOAD_JSON_TO_S3"},
                ),
                mock.call(
                    f"Successfully uploaded to: {s3_file_path}",
                    extra={"event": "UPLOADED_JSON_TO_S3"},
                ),
            ]
        )
