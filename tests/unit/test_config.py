from datetime import datetime

import pytest
from dateutil.tz import tzutc
from prmods.domain.ods_portal.ods_data_fetcher import ODS_PORTAL_SEARCH_URL
from prmods.pipeline.ods_downloader.config import OdsPortalConfig, MissingEnvironmentVariable


def test_reads_from_environment_variables_and_converts_to_required_format():
    environment = {
        "S3_ENDPOINT_URL": "https://an.endpoint:3000",
        "OUTPUT_BUCKET": "output-bucket",
        "MAPPING_BUCKET": "mapping-bucket",
        "SEARCH_URL": "https://an.endpoint:3000",
        "DATE_ANCHOR": "2020-01-30T18:44:49Z",
    }

    expected_config = OdsPortalConfig(
        s3_endpoint_url="https://an.endpoint:3000",
        mapping_bucket="mapping-bucket",
        output_bucket="output-bucket",
        search_url="https://an.endpoint:3000",
        date_anchor=datetime(
            year=2020, month=1, day=30, hour=18, minute=44, second=49, tzinfo=tzutc()
        ),
    )

    actual_config = OdsPortalConfig.from_environment_variables(environment)

    assert actual_config == expected_config


def test_read_config_from_environment_when_optional_parameters_are_not_set():
    environment = {
        "OUTPUT_BUCKET": "output-bucket",
        "MAPPING_BUCKET": "mapping-bucket",
        "DATE_ANCHOR": "2020-01-30T18:44:49Z",
    }

    expected_config = OdsPortalConfig(
        mapping_bucket="mapping-bucket",
        output_bucket="output-bucket",
        search_url=ODS_PORTAL_SEARCH_URL,
        date_anchor=datetime(
            year=2020, month=1, day=30, hour=18, minute=44, second=49, tzinfo=tzutc()
        ),
    )

    actual_config = OdsPortalConfig.from_environment_variables(environment)

    assert actual_config == expected_config


def test_error_from_environment_when_required_fields_are_not_set():
    environment = {
        "OUTPUT_TRANSFER_DATA_BUCKET": "output-transfer-data-bucket",
        "INPUT_TRANSFER_DATA_BUCKET": "input-transfer-data-bucket",
    }

    with pytest.raises(MissingEnvironmentVariable):
        OdsPortalConfig.from_environment_variables(environment)
