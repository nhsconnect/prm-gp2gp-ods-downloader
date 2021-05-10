from datetime import datetime

from prmods.domain.ods_portal.sources import ODS_PORTAL_SEARCH_URL
from prmods.pipeline.ods_downloader.config import OdsPortalConfig


def test_read_config_from_environment():
    environment = {
        "S3_ENDPOINT_URL": "https://an.endpoint:3000",
        "OUTPUT_BUCKET": "output-bucket",
        "MAPPING_BUCKET": "mapping-bucket",
        "SEARCH_URL": "https://an.endpoint:3000",
    }

    expected_config = OdsPortalConfig(
        s3_endpoint_url="https://an.endpoint:3000",
        mapping_bucket="mapping-bucket",
        output_bucket="output-bucket",
        search_url="https://an.endpoint:3000",
    )

    actual_config = OdsPortalConfig.from_environment_variables(environment)

    assert actual_config == expected_config


def test_read_config_from_environment_when_optional_parameters_are_not_set():
    environment = {
        "OUTPUT_BUCKET": "output-bucket",
        "MAPPING_BUCKET": "mapping-bucket",
    }

    expected_config = OdsPortalConfig(
        mapping_bucket="mapping-bucket",
        output_bucket="output-bucket",
        search_url=ODS_PORTAL_SEARCH_URL,
    )

    actual_config = OdsPortalConfig.from_environment_variables(environment)

    assert actual_config == expected_config


def test_month_or_year_should_override_default_value_when_set():
    environment = {
        "OUTPUT_BUCKET": "output-bucket",
        "MAPPING_BUCKET": "mapping-bucket",
        "MONTH": 6,
        "YEAR": 2020,
    }

    expected_config = OdsPortalConfig(
        mapping_bucket="mapping-bucket",
        output_bucket="output-bucket",
        search_url=ODS_PORTAL_SEARCH_URL,
        month=6,
        year=2020,
    )
    actual_config = OdsPortalConfig.from_environment_variables(environment)

    assert actual_config == expected_config


def test_month_or_year_should_set_default_values_based_on_current_date():
    environment = {
        "OUTPUT_BUCKET": "output-bucket",
        "MAPPING_BUCKET": "mapping-bucket",
    }

    expected_config = OdsPortalConfig(
        mapping_bucket="mapping-bucket",
        output_bucket="output-bucket",
        search_url=ODS_PORTAL_SEARCH_URL,
        month=datetime.utcnow().month,
        year=datetime.utcnow().year,
    )

    actual_config = OdsPortalConfig.from_environment_variables(environment)
    assert actual_config == expected_config
