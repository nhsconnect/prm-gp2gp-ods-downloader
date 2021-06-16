from typing import List, Iterable
from warnings import warn

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.ods_portal_data_fetcher import (
    OdsPortalDataFetcher,
    OrganisationDetails,
)
from prmods.domain.ods_portal.organisation_metadata import PracticeDetails


class Gp2gpOrganisationMetadataService:
    def __init__(self, data_fetcher: OdsPortalDataFetcher):
        self._data_fetcher = data_fetcher

    def retrieve_practices_with_asids(self, asid_lookup: AsidLookup) -> List[PracticeDetails]:
        practices = self._data_fetcher.fetch_all_practices()
        unique_practices = self._remove_duplicated_organisations(practices)

        return list(self._enrich_practices_with_asids(unique_practices, asid_lookup))

    @staticmethod
    def _enrich_practices_with_asids(
        practices: Iterable[OrganisationDetails], asid_lookup: AsidLookup
    ):
        for practice in practices:
            if asid_lookup.has_ods(practice.ods_code):
                yield PracticeDetails(
                    asids=asid_lookup.get_asids(practice.ods_code),
                    ods_code=practice.ods_code,
                    name=practice.name,
                )
            else:
                warn(f"ODS code not found in ASID mapping: {practice.ods_code}", RuntimeWarning)

    @staticmethod
    def _remove_duplicated_organisations(
        practices: List[OrganisationDetails],
    ) -> Iterable[OrganisationDetails]:
        seen_ods = set()
        for practice in practices:
            if practice.ods_code not in seen_ods:
                yield practice
            seen_ods.add(practice.ods_code)
