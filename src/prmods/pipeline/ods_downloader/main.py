import logging

from dataclasses import asdict

from os import environ

import boto3

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.organisation_metadata import OrganisationMetadataConstructor
from prmods.pipeline.ods_downloader.config import OdsPortalConfig

from prmods.domain.ods_portal.ods_data_fetcher import (
    OdsDataFetcher,
    PRACTICE_SEARCH_PARAMS,
    CCG_SEARCH_PARAMS,
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
    asid_lookup = AsidLookup(raw_asid_lookup)

    data_fetcher = OdsDataFetcher(search_url=config.search_url)
    organisation_metadata_constructor = OrganisationMetadataConstructor(data_fetcher, asid_lookup)

    organisation_metadata = (
        organisation_metadata_constructor.create_organisation_metadata_from_practice_and_ccg_lists()
    )

    s3_manager.write_json(metadata_output_s3_path, asdict(organisation_metadata))


if __name__ == "__main__":
    main()
