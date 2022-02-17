from datetime import datetime


class OdsDownloaderS3UriResolver:
    _ORG_METADATA_VERSION = "v3"
    _ORG_METADATA_FILE_NAME = "organisationMetadata.json"
    _ASID_LOOKUP_FILE_NAME = "asidLookup.csv.gz"

    def __init__(self, asid_lookup_bucket: str, ods_metadata_bucket):
        self._asid_lookup_bucket = asid_lookup_bucket
        self._ods_metadata_bucket = ods_metadata_bucket

    def asid_lookup(self, date_anchor: datetime) -> str:
        date_prefix = f"{date_anchor.year}/{date_anchor.month}"
        return f"s3://{self._asid_lookup_bucket}/{date_prefix}/{self._ASID_LOOKUP_FILE_NAME}"

    def ods_metadata(self, date_anchor: datetime) -> str:
        date_prefix = f"{date_anchor.year}/{date_anchor.month}"
        return (
            f"s3://{self._ods_metadata_bucket}/{self._ORG_METADATA_VERSION}/{date_prefix}"
            f"/{self._ORG_METADATA_FILE_NAME}"
        )
