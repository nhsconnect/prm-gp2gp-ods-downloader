from dataclasses import asdict

import boto3

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.metadata_service import (
    Gp2gpOrganisationMetadataService,
    MetadataServiceObservabilityProbe,
    OrganisationMetadata,
)
from prmods.domain.ods_portal.ods_portal_client import OdsPortalClient
from prmods.domain.ods_portal.ods_portal_data_fetcher import OdsPortalDataFetcher
from prmods.pipeline.config import OdsPortalConfig
from prmods.utils.io.s3 import S3DataManager

VERSION = "v3"


class OdsDownloader:
    def __init__(self, config: OdsPortalConfig):
        s3 = boto3.resource("s3", endpoint_url=config.s3_endpoint_url)
        self._s3_manager = S3DataManager(s3)

        self._config = config

    def _s3_date_prefix(self) -> str:
        return f"{self._config.date_anchor.year}/{self._config.date_anchor.month}"

    def _read_asid_lookup(self) -> AsidLookup:
        asid_lookup_s3_path = (
            f"s3://{self._config.mapping_bucket}/{self._s3_date_prefix()}/asidLookup.csv.gz"
        )
        raw_asid_lookup = self._s3_manager.read_gzip_csv(asid_lookup_s3_path)
        return AsidLookup.from_spine_directory_format(raw_asid_lookup)

    def _write_ods_metadata(self, organisation_metadata: OrganisationMetadata):
        metadata_output_s3_path = (
            f"s3://{self._config.output_bucket}/{VERSION}/{self._s3_date_prefix()}"
            f"/organisationMetadata.json"
        )

        output_metadata = {
            "date-anchor": self._config.date_anchor.isoformat(),
            "build-tag": self._config.build_tag,
        }
        self._s3_manager.write_json(
            metadata_output_s3_path, asdict(organisation_metadata), output_metadata
        )

    def run(self):
        ods_client = OdsPortalClient(search_url=self._config.search_url)
        ods_data_fetcher = OdsPortalDataFetcher(ods_client=ods_client)
        probe = MetadataServiceObservabilityProbe()
        metadata_service = Gp2gpOrganisationMetadataService(
            data_fetcher=ods_data_fetcher, observability_probe=probe
        )

        asid_lookup = self._read_asid_lookup()
        practice_metadata = metadata_service.retrieve_practices_with_asids(asid_lookup=asid_lookup)
        ccg_metadata = metadata_service.retrieve_ccg_practice_allocations(
            canonical_practice_list=practice_metadata
        )
        organisation_metadata = OrganisationMetadata.from_practice_and_ccg_lists(
            practice_metadata,
            ccg_metadata,
            self._config.date_anchor.year,
            self._config.date_anchor.month,
        )

        self._write_ods_metadata(organisation_metadata)
