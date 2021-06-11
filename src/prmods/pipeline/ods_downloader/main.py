import logging

from dataclasses import asdict

from os import environ

import boto3

from prmods.pipeline.ods_downloader.config import OdsPortalConfig

from prmods.domain.ods_portal.sources import (
    OdsDataFetcher,
    construct_organisation_metadata_from_practice_and_ccg_lists,
    PRACTICE_SEARCH_PARAMS,
    CCG_SEARCH_PARAMS,
    construct_practice_metadata_from_ods_portal_response,
    construct_ccg_metadata_from_ods_portal_response,
    construct_asid_to_ods_mappings,
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

    data_fetcher = OdsDataFetcher(search_url=config.search_url)

    asid_lookup = s3_manager.read_gzip_csv(asid_lookup_s3_path)

    practice_data_response = data_fetcher.fetch_organisation_data(PRACTICE_SEARCH_PARAMS)
    practice_metadata = construct_practice_metadata_from_ods_portal_response(
        practice_data_response, construct_asid_to_ods_mappings(asid_lookup)
    )

    ccg_data_response = data_fetcher.fetch_organisation_data(CCG_SEARCH_PARAMS)
    ccg_metadata = construct_ccg_metadata_from_ods_portal_response(ccg_data_response, data_fetcher)

    organisation_metadata = construct_organisation_metadata_from_practice_and_ccg_lists(
        practice_metadata,
        ccg_metadata,
    )
    s3_manager.write_json(metadata_output_s3_path, asdict(organisation_metadata))


if __name__ == "__main__":
    main()
