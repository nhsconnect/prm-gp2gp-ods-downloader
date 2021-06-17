import logging
from dataclasses import asdict
from os import environ
import boto3

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.metadata_service import (
    Gp2gpOrganisationMetadataService,
    OrganisationMetadata,
)
from prmods.domain.ods_portal.ods_portal_data_fetcher import OdsPortalDataFetcher
from prmods.pipeline.ods_downloader.config import OdsPortalConfig

from prmods.domain.ods_portal.ods_portal_client import (
    OdsPortalClient,
)
from prmods.utils.io.s3 import S3DataManager

logger = logging.getLogger(__name__)

VERSION = "v2"


def main():
    config = OdsPortalConfig.from_environment_variables(environ)

    logging.basicConfig(level=logging.INFO)

    logger.info(config.s3_endpoint_url)

    date_prefix = f"{config.date_anchor.year}/{config.date_anchor.month}"
    asid_lookup_s3_path = f"s3://{config.mapping_bucket}/{date_prefix}/asidLookup.csv.gz"
    metadata_output_s3_path = (
        f"s3://{config.output_bucket}/{VERSION}/{date_prefix}" f"/organisationMetadata.json"
    )

    logger.info("using asid lookup file located in : " + asid_lookup_s3_path)
    logger.info("output location is: " + metadata_output_s3_path)

    s3 = boto3.resource("s3", endpoint_url=config.s3_endpoint_url)
    s3_manager = S3DataManager(s3)

    raw_asid_lookup = s3_manager.read_gzip_csv(asid_lookup_s3_path)
    asid_lookup = AsidLookup.from_spine_directory_format(raw_asid_lookup)

    ods_client = OdsPortalClient(search_url=config.search_url)
    ods_data_fetcher = OdsPortalDataFetcher(ods_client=ods_client)
    metadata_service = Gp2gpOrganisationMetadataService(data_fetcher=ods_data_fetcher)

    practice_metadata = metadata_service.retrieve_practices_with_asids(asid_lookup=asid_lookup)
    ccg_metadata = metadata_service.retrieve_ccg_practice_allocations()

    organisation_metadata = OrganisationMetadata.from_practice_and_ccg_lists(
        practice_metadata, ccg_metadata
    )

    s3_manager.write_json(metadata_output_s3_path, asdict(organisation_metadata))


if __name__ == "__main__":
    main()
