from dataclasses import dataclass

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


class OdsPortalDataFetcher:
    def __init__(self, ods_client: OdsPortalClient):
        self._ods_client = ods_client

    def fetch_all_practices(self):
        practice_data_response = self._ods_client.fetch_organisation_data(PRACTICE_SEARCH_PARAMS)
        return [
            OrganisationDetails(name=practice["Name"], ods_code=practice["OrgId"])
            for practice in practice_data_response
        ]
