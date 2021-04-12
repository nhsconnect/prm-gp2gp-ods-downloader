from unittest.mock import MagicMock
from prmods.utils.io.json import upload_json_object


def test_uploads_dictionary():
    mock_s3_object = MagicMock()
    upload_json_object(mock_s3_object, '{"status": "open"}')
    expected_body = b'"{\\"status\\": \\"open\\"}"'
    mock_s3_object.put.assert_called_once_with(Body=expected_body, ContentType="application/json")
