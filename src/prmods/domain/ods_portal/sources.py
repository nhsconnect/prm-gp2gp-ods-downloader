import json
from collections import defaultdict
from datetime import datetime
from typing import Iterable, List, DefaultDict
from warnings import warn

import requests
from dateutil.tz import tzutc

from prmods.domain.ods_portal.models import (
    CcgDetails,
    OrganisationMetadata,
    PracticeDetails,
)

ODS_PORTAL_SEARCH_URL = "https://directory.spineservices.nhs.uk/ORD/2-0-0/organisations"
PRACTICE_SEARCH_PARAMS = {
    "PrimaryRoleId": "RO177",
    "Status": "Active",
    "NonPrimaryRoleId": "RO76",
    "Limit": "1000",
}
CCG_SEARCH_PARAMS = {
    "PrimaryRoleId": "RO98",
    "Status": "Active",
    "Limit": "1000",
}
CCG_PRACTICES_SEARCH_PARAMS = {
    "RelTypeId": "RE4",
    "RelStatus": "active",
    "Limit": "1000",
}

NEXT_PAGE_HEADER = "Next-Page"


class OdsPortalException(Exception):
    def __init__(self, message, status_code):
        super(OdsPortalException, self).__init__(message)
        self.status_code = status_code


class OdsDataFetcher:
    def __init__(self, client=requests, search_url=ODS_PORTAL_SEARCH_URL):
        self._search_url = search_url
        self._client = client

    def fetch_organisation_data(self, params):
        response_data = list(self._iterate_organisation_data(params))
        return response_data

    def _iterate_organisation_data(self, params):
        try:
            response = self._client.get(self._search_url, params)
            yield from self._process_practice_data_response(response)

            while NEXT_PAGE_HEADER in response.headers:
                response = self._client.get(response.headers[NEXT_PAGE_HEADER])
                yield from self._process_practice_data_response(response)
        except StopIteration:
            pass

    @classmethod
    def _process_practice_data_response(cls, response):
        if response.status_code != 200:
            raise OdsPortalException("Unable to fetch organisation data", response.status_code)
        return json.loads(response.content)["Organisations"]


def _is_ods_in_mapping(
    ods_code: str,
    asid_mapping: dict,
):
    if ods_code in asid_mapping:
        return True
    else:
        warn(f"ODS code not found in ASID mapping: {ods_code}", RuntimeWarning)
        return False


def construct_organisation_metadata_from_practice_and_ccg_lists(
    practice_metadata: List[PracticeDetails], ccg_metadata: List[CcgDetails]
) -> OrganisationMetadata:
    return OrganisationMetadata(
        generated_on=datetime.now(tzutc()), practices=practice_metadata, ccgs=ccg_metadata
    )


def construct_practice_metadata_from_ods_portal_response(
    practice_data_response: Iterable[dict], asid_mapping: dict
) -> List[PracticeDetails]:
    unique_practices = _remove_duplicated_organisations(practice_data_response)

    return [
        PracticeDetails(asids=asid_mapping[p["OrgId"]], ods_code=p["OrgId"], name=p["Name"])
        for p in unique_practices
        if _is_ods_in_mapping(p["OrgId"], asid_mapping)
    ]


def construct_ccg_metadata_from_ods_portal_response(
    ccg_data_response: Iterable[dict], data_fetcher: OdsDataFetcher
) -> List[CcgDetails]:
    unique_ccgs = _remove_duplicated_organisations(ccg_data_response)

    return [
        CcgDetails(
            ods_code=c["OrgId"],
            name=c["Name"],
            practices=_fetch_practices_for_a_ccg(c["OrgId"], data_fetcher),
        )
        for c in unique_ccgs
    ]


def _fetch_practices_for_a_ccg(ccg_ods_code: str, data_fetcher: OdsDataFetcher) -> List[str]:
    CCG_PRACTICES_SEARCH_PARAMS.update({"TargetOrgId": ccg_ods_code})

    ccg_practices_response = data_fetcher.fetch_organisation_data(CCG_PRACTICES_SEARCH_PARAMS)
    ccg_practices = [p["OrgId"] for p in ccg_practices_response]
    return ccg_practices


def _remove_duplicated_organisations(raw_organisations: Iterable[dict]) -> Iterable[dict]:
    return {obj["OrgId"]: obj for obj in raw_organisations}.values()


def construct_asid_to_ods_mappings(raw_mappings: Iterable[dict]) -> defaultdict:
    complete_mapping: DefaultDict[str, List[str]] = defaultdict(list)
    for mapping in raw_mappings:
        complete_mapping[mapping["NACS"]].append(mapping["ASID"])
    return complete_mapping
