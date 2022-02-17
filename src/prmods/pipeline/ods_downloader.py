from dataclasses import asdict
from datetime import datetime

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


class OdsDownloaderS3UriResolver:
    VERSION = "v3"

    def __init__(self, asid_lookup_bucket: str, ods_metadata_bucket):
        self._asid_lookup_bucket = asid_lookup_bucket
        self._ods_metadata_bucket = ods_metadata_bucket

    def asid_lookup(self, date_anchor: datetime) -> str:
        date_prefix = f"{date_anchor.year}/{date_anchor.month}"
        return f"s3://{self._asid_lookup_bucket}/{date_prefix}/asidLookup.csv.gz"

    def ods_metadata(self, date_anchor: datetime) -> str:
        date_prefix = f"{date_anchor.year}/{date_anchor.month}"
        return (
            f"s3://{self._ods_metadata_bucket}/{self.VERSION}/{date_prefix}"
            f"/organisationMetadata.json"
        )


class OdsDownloader:
    def __init__(self, config: OdsPortalConfig):
        s3 = boto3.resource("s3", endpoint_url=config.s3_endpoint_url)
        self._s3_manager = S3DataManager(s3)

        self._config = config
        self._uris = OdsDownloaderS3UriResolver(
            asid_lookup_bucket=self._config.mapping_bucket,
            ods_metadata_bucket=self._config.output_bucket,
        )

        ods_client = OdsPortalClient(search_url=self._config.search_url)
        ods_data_fetcher = OdsPortalDataFetcher(ods_client=ods_client)
        probe = MetadataServiceObservabilityProbe()
        self._metadata_service = Gp2gpOrganisationMetadataService(
            data_fetcher=ods_data_fetcher, observability_probe=probe
        )

    def _read_asid_lookup(self) -> AsidLookup:
        asid_lookup_s3_path = self._uris.asid_lookup(self._config.date_anchor)
        raw_asid_lookup = self._s3_manager.read_gzip_csv(asid_lookup_s3_path)
        return AsidLookup.from_spine_directory_format(raw_asid_lookup)

    def _write_ods_metadata(self, organisation_metadata: OrganisationMetadata):
        metadata_output_s3_path = self._uris.ods_metadata(self._config.date_anchor)
        output_metadata = {
            "date-anchor": self._config.date_anchor.isoformat(),
            "build-tag": self._config.build_tag,
        }
        self._s3_manager.write_json(
            metadata_output_s3_path, asdict(organisation_metadata), output_metadata
        )

    def run(self):
        asid_lookup = self._read_asid_lookup()
        practice_metadata = self._metadata_service.retrieve_practices_with_asids(
            asid_lookup=asid_lookup
        )
        ccg_metadata = self._metadata_service.retrieve_ccg_practice_allocations(
            canonical_practice_list=practice_metadata
        )
        organisation_metadata = OrganisationMetadata.from_practice_and_ccg_lists(
            practice_metadata,
            ccg_metadata,
            self._config.date_anchor.year,
            self._config.date_anchor.month,
        )
        self._write_ods_metadata(organisation_metadata)
