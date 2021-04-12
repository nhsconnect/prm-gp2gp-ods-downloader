from prmods.domain.ods_portal.sources import ODS_PORTAL_SEARCH_URL
from prmods.pipeline.ods_downloader.config import OdsPortalConfig


def test_read_config_from_environment():
    environment = {
        "S3_ENDPOINT_URL": "https://an.endpoint:3000",
        "OUTPUT_FILE": "s3://bucket/output",
        "MAPPING_FILE": "s3://bucket/mapping",
        "SEARCH_URL": "https://an.endpoint:3000",
    }

    expected_config = OdsPortalConfig(
        s3_endpoint_url="https://an.endpoint:3000",
        mapping_file="s3://bucket/mapping",
        output_file="s3://bucket/output",
        search_url="https://an.endpoint:3000",
    )

    actual_config = OdsPortalConfig.from_environment_variables(environment)

    assert actual_config == expected_config


def test_read_config_from_environment_when_optional_parameters_are_not_set():
    environment = {
        "OUTPUT_FILE": "s3://bucket/output",
        "MAPPING_FILE": "s3://bucket/mapping",
    }

    expected_config = OdsPortalConfig(
        mapping_file="s3://bucket/mapping",
        output_file="s3://bucket/output",
        search_url=ODS_PORTAL_SEARCH_URL,
    )

    actual_config = OdsPortalConfig.from_environment_variables(environment)

    assert actual_config == expected_config
