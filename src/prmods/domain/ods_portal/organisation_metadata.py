from dataclasses import dataclass
from datetime import datetime
from typing import List, Iterable, DefaultDict
from warnings import warn
from dateutil.tz import tzutc
from collections import defaultdict

from prmods.domain.ods_portal.ods_data_fetcher import OdsDataFetcher, CCG_PRACTICES_SEARCH_PARAMS


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
