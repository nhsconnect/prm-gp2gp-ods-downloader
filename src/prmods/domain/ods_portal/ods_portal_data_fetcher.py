from dataclasses import dataclass
from typing import List

from prmods.domain.ods_portal.ods_portal_client import OdsPortalClient


@dataclass
class OrganisationDetails:
    ods_code: str
    name: str


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


class OdsPortalDataFetcher:
    def __init__(self, ods_client: OdsPortalClient):
        self._ods_client = ods_client

    def fetch_all_practices(self) -> List[OrganisationDetails]:
        return self._fetch_organisation_details(PRACTICE_SEARCH_PARAMS)

    def fetch_all_ccgs(self) -> List[OrganisationDetails]:
        return self._fetch_organisation_details(CCG_SEARCH_PARAMS)

    def fetch_practices_for_ccg(self, ccg_ods_code: str) -> List[OrganisationDetails]:
        ccg_practices_search_params = CCG_PRACTICES_SEARCH_PARAMS | {"TargetOrgId": ccg_ods_code}
        return self._fetch_organisation_details(ccg_practices_search_params)

    def _fetch_organisation_details(self, params):
        response = self._ods_client.fetch_organisation_data(params)
        return [
            OrganisationDetails(name=organisation["Name"], ods_code=organisation["OrgId"])
            for organisation in response
        ]
