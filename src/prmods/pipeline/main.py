import logging
from dataclasses import asdict
from os import environ
import boto3

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.metadata_service import (
    Gp2gpOrganisationMetadataService,
    OrganisationMetadata,
    MetadataServiceObservabilityProbe,
)
from prmods.domain.ods_portal.ods_portal_data_fetcher import OdsPortalDataFetcher
from prmods.pipeline.config import OdsPortalConfig

from prmods.domain.ods_portal.ods_portal_client import (
    OdsPortalClient,
)
from prmods.utils.io.json_formatter import JsonFormatter
from prmods.utils.io.s3 import S3DataManager

logger = logging.getLogger("prmods")

VERSION = "v2"


def _setup_logger():
    logger.setLevel(logging.INFO)
    formatter = JsonFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main():
    _setup_logger()

    config = OdsPortalConfig.from_environment_variables(environ)

    output_metadata = {"date-anchor": config.date_anchor.isoformat()}

    date_prefix = f"{config.date_anchor.year}/{config.date_anchor.month}"
    asid_lookup_s3_path = f"s3://{config.mapping_bucket}/{date_prefix}/asidLookup.csv.gz"
    metadata_output_s3_path = (
        f"s3://{config.output_bucket}/{VERSION}/{date_prefix}" f"/organisationMetadata.json"
    )

    s3 = boto3.resource("s3", endpoint_url=config.s3_endpoint_url)
    s3_manager = S3DataManager(s3)

    raw_asid_lookup = s3_manager.read_gzip_csv(asid_lookup_s3_path)
    asid_lookup = AsidLookup.from_spine_directory_format(raw_asid_lookup)

    ods_client = OdsPortalClient(search_url=config.search_url)
    ods_data_fetcher = OdsPortalDataFetcher(ods_client=ods_client)
    probe = MetadataServiceObservabilityProbe()
    metadata_service = Gp2gpOrganisationMetadataService(
        data_fetcher=ods_data_fetcher, observability_probe=probe
    )

    practice_metadata = metadata_service.retrieve_practices_with_asids(asid_lookup=asid_lookup)
    ccg_metadata = metadata_service.retrieve_ccg_practice_allocations(
        canonical_practice_list=practice_metadata
    )

    organisation_metadata = OrganisationMetadata.from_practice_and_ccg_lists(
        practice_metadata, ccg_metadata
    )

    s3_manager.write_json(metadata_output_s3_path, asdict(organisation_metadata), output_metadata)


if __name__ == "__main__":
    main()
