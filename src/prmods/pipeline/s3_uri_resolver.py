from datetime import datetime

from dateutil.relativedelta import relativedelta


class OdsDownloaderS3UriResolver:
    _ORG_METADATA_VERSION = "v3"
    _ORG_METADATA_FILE_NAME = "organisationMetadata.json"
    _ASID_LOOKUP_FILE_NAME = "asidLookup.csv.gz"

    def __init__(self, asid_lookup_bucket: str, ods_metadata_bucket):
        self._asid_lookup_bucket = asid_lookup_bucket
        self._ods_metadata_bucket = ods_metadata_bucket

    @staticmethod
    def _s3_path(*fragments):
        return "s3://" + "/".join(fragments)

    def asid_lookup(self, date_anchor: datetime) -> str:
        return self._s3_path(
            self._asid_lookup_bucket,
            str(date_anchor.year),
            str(date_anchor.month),
            self._ASID_LOOKUP_FILE_NAME,
        )

    def previous_month_asid_lookup(self, date_anchor: datetime) -> str:
        previous_month_date_anchor = date_anchor - relativedelta(months=1)
        return self.asid_lookup(previous_month_date_anchor)

    def ods_metadata(self, date_anchor: datetime) -> str:
        return self._s3_path(
            self._ods_metadata_bucket,
            self._ORG_METADATA_VERSION,
            str(date_anchor.year),
            str(date_anchor.month),
            self._ORG_METADATA_FILE_NAME,
        )
