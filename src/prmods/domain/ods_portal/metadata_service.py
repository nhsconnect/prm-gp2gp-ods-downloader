from typing import List, Iterable
from warnings import warn

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.ods_portal_data_fetcher import (
    OdsPortalDataFetcher,
    OrganisationDetails,
)
from prmods.domain.ods_portal.organisation_metadata import PracticeDetails, CcgDetails


class Gp2gpOrganisationMetadataService:
    def __init__(self, data_fetcher: OdsPortalDataFetcher):
        self._data_fetcher = data_fetcher

    def retrieve_practices_with_asids(self, asid_lookup: AsidLookup) -> List[PracticeDetails]:
        practices = self._data_fetcher.fetch_all_practices()
        unique_practices = self._remove_duplicate_organisations(practices)

        return list(self._enrich_practices_with_asids(unique_practices, asid_lookup))

    def retrieve_ccg_practice_allocations(self) -> List[CcgDetails]:
        ccgs = self._data_fetcher.fetch_all_ccgs()
        unique_ccgs = self._remove_duplicate_organisations(ccgs)

        return [self._fetch_ccg_practice_allocation(ccg) for ccg in unique_ccgs]

    def _fetch_ccg_practice_allocation(self, ccg):
        ccg_practices = self._data_fetcher.fetch_practices_for_ccg(ccg.ods_code)
        return CcgDetails(
            ods_code=ccg.ods_code,
            name=ccg.name,
            practices=[practice.ods_code for practice in ccg_practices],
        )

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
    def _remove_duplicate_organisations(
        organisations: List[OrganisationDetails],
    ) -> Iterable[OrganisationDetails]:
        seen_ods = set()
        for organisation in organisations:
            if organisation.ods_code not in seen_ods:
                yield organisation
            seen_ods.add(organisation.ods_code)
