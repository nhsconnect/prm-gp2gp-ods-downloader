from dataclasses import dataclass
from typing import List, Iterable, Set
from warnings import warn
from datetime import datetime
from dateutil.tz import tzutc

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.ods_portal_data_fetcher import (
    OrganisationDetails,
    OdsDataSource,
)


@dataclass
class CcgDetails:
    ods_code: str
    name: str
    practices: List[str]


@dataclass
class PracticeDetails:
    ods_code: str
    name: str
    asids: List[str]


@dataclass
class OrganisationMetadata:
    generated_on: datetime
    practices: List[PracticeDetails]
    ccgs: List[CcgDetails]

    @classmethod
    def from_practice_and_ccg_lists(cls, practices: List[PracticeDetails], ccgs: List[CcgDetails]):
        return cls(generated_on=datetime.now(tzutc()), practices=practices, ccgs=ccgs)


class Gp2gpOrganisationMetadataService:
    def __init__(self, data_fetcher: OdsDataSource):
        self._data_fetcher = data_fetcher

    def retrieve_practices_with_asids(self, asid_lookup: AsidLookup) -> List[PracticeDetails]:
        practices = self._data_fetcher.fetch_all_practices()
        unique_practices = self._remove_duplicate_organisations(practices)

        return list(self._enrich_practices_with_asids(unique_practices, asid_lookup))

    def retrieve_ccg_practice_allocations(
        self, canonical_practice_list: List[PracticeDetails]
    ) -> List[CcgDetails]:
        ccgs = self._data_fetcher.fetch_all_ccgs()
        unique_ccgs = self._remove_duplicate_organisations(ccgs)
        canonical_practice_ods_codes = {practice.ods_code for practice in canonical_practice_list}

        return [
            self._fetch_ccg_practice_allocation(ccg, canonical_practice_ods_codes)
            for ccg in unique_ccgs
        ]

    def _fetch_ccg_practice_allocation(
        self, ccg: OrganisationDetails, canonical_practice_ods_codes: Set[str]
    ):
        ccg_practices = self._data_fetcher.fetch_practices_for_ccg(ccg.ods_code)

        return CcgDetails(
            ods_code=ccg.ods_code,
            name=ccg.name,
            practices=[
                practice.ods_code
                for practice in ccg_practices
                if practice.ods_code in canonical_practice_ods_codes
            ],
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
            else:
                warn(f"Duplicate ODS code found: {organisation.ods_code}", RuntimeWarning)
            seen_ods.add(organisation.ods_code)
