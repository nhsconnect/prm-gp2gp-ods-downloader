from dataclasses import dataclass
from datetime import datetime
from typing import List, Iterable, DefaultDict
from warnings import warn
from dateutil.tz import tzutc
from collections import defaultdict

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.ods_data_fetcher import (
    OdsDataFetcher,
    CCG_PRACTICES_SEARCH_PARAMS,
    PRACTICE_SEARCH_PARAMS,
    CCG_SEARCH_PARAMS,
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


class PracticeDetailsList:
    def create_practice_metadata_from_ods_portal_response(
        self, data_fetcher: OdsDataFetcher, asid_lookup: AsidLookup
    ) -> List[PracticeDetails]:
        practice_data_response = data_fetcher.fetch_organisation_data(PRACTICE_SEARCH_PARAMS)
        unique_practices = OrganisationMetadataConstructor.remove_duplicated_organisations(
            practice_data_response
        )

        return [
            PracticeDetails(
                asids=asid_lookup.ods_asid_mapping[p["OrgId"]], ods_code=p["OrgId"], name=p["Name"]
            )
            for p in unique_practices
            if asid_lookup.is_ods_in_mapping(p["OrgId"])
        ]


@dataclass
class OrganisationMetadata:
    generated_on: datetime
    practices: List[PracticeDetails]
    ccgs: List[CcgDetails]


class OrganisationMetadataConstructor:
    def __init__(self, data_fetcher: OdsDataFetcher, asid_lookup: AsidLookup):
        self._data_fetcher = data_fetcher
        self.asid_lookup = asid_lookup

    def create_organisation_metadata_from_practice_and_ccg_lists(self) -> OrganisationMetadata:
        practice_metadata = PracticeDetailsList().create_practice_metadata_from_ods_portal_response(
            self._data_fetcher, self.asid_lookup
        )
        ccg_metadata = self.create_ccg_metadata_from_ods_portal_response()

        return OrganisationMetadata(
            generated_on=datetime.now(tzutc()), practices=practice_metadata, ccgs=ccg_metadata
        )

    def create_ccg_metadata_from_ods_portal_response(self) -> List[CcgDetails]:
        ccg_data_response = self._data_fetcher.fetch_organisation_data(CCG_SEARCH_PARAMS)
        unique_ccgs = self.remove_duplicated_organisations(ccg_data_response)

        return [
            CcgDetails(
                ods_code=c["OrgId"],
                name=c["Name"],
                practices=self._fetch_practices_for_a_ccg(c["OrgId"], self._data_fetcher),
            )
            for c in unique_ccgs
        ]

    def _fetch_practices_for_a_ccg(
        self, ccg_ods_code: str, data_fetcher: OdsDataFetcher
    ) -> List[str]:
        CCG_PRACTICES_SEARCH_PARAMS.update({"TargetOrgId": ccg_ods_code})

        ccg_practices_response = data_fetcher.fetch_ccg_practice_data(CCG_PRACTICES_SEARCH_PARAMS)
        ccg_practices = [p["OrgId"] for p in ccg_practices_response]
        return ccg_practices

    @staticmethod
    def remove_duplicated_organisations(raw_organisations: Iterable[dict]) -> Iterable[dict]:
        return {obj["OrgId"]: obj for obj in raw_organisations}.values()
