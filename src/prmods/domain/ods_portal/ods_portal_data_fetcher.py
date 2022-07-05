from dataclasses import dataclass
from typing import List, Optional, Protocol

from prmods.domain.ods_portal.ods_portal_client import OdsPortalClient


@dataclass
class OrganisationDetails:
    ods_code: str
    name: str


PRACTICE_SEARCH_PARAMS_NON_PRISONS_DEPRECATED = {
    "PrimaryRoleId": "RO177",
    "Status": "Active",
    "NonPrimaryRoleId": "RO76",
    "Limit": "1000",
}

ROLES_FOR_COST_CENTRE_PRACTICES = ",".join(
    [
        "RO177",  # PRESCRIBING COST CENTRE
        "RO82",  # PRISON PRESCRIBING COST CENTRE
        "RO257",  # SECURE TRAINING CENTRE PRESCRIBING COST CENTRE
        "RO251",  # IMMIGRATION REMOVAL CENTRE PRESCRIBING COST CENTRE
        "RO260",  # YOUNG OFFENDER INSTITUTION PRESCRIBING COST CENTRE
    ]
)

PRACTICE_SEARCH_PARAMS_WITH_MULTIPLE_ROLES = {
    "Status": "Active",
    "Roles": ROLES_FOR_COST_CENTRE_PRACTICES,
    "Limit": "1000",
}

ICB_SEARCH_PARAMS = {
    "PrimaryRoleId": "RO98",
    "Status": "Active",
    "Limit": "1000",
}

ICB_PRACTICES_SEARCH_PARAMS = {
    "RelTypeId": "RE4",
    "RelStatus": "active",
    "Limit": "1000",
}


class OdsDataSource(Protocol):
    def fetch_all_practices(
        self, show_prison_practices_toggle: Optional[bool] = False
    ) -> List[OrganisationDetails]:
        ...

    def fetch_all_icbs(self) -> List[OrganisationDetails]:
        ...

    def fetch_practices_for_icb(self, icb_ods_code: str) -> List[OrganisationDetails]:
        ...


class OdsPortalDataFetcher:
    def __init__(self, ods_client: OdsPortalClient):
        self._ods_client = ods_client

    def fetch_all_practices(
        self, show_prison_practices_toggle: Optional[bool] = False
    ) -> List[OrganisationDetails]:
        if show_prison_practices_toggle is True:
            return self._fetch_organisation_details(PRACTICE_SEARCH_PARAMS_WITH_MULTIPLE_ROLES)
        else:
            return self._fetch_organisation_details(PRACTICE_SEARCH_PARAMS_NON_PRISONS_DEPRECATED)

    def fetch_all_icbs(self) -> List[OrganisationDetails]:
        return self._fetch_organisation_details(ICB_SEARCH_PARAMS)

    def fetch_practices_for_icb(self, icb_ods_code: str) -> List[OrganisationDetails]:
        icb_practices_search_params = ICB_PRACTICES_SEARCH_PARAMS | {"TargetOrgId": icb_ods_code}
        return self._fetch_organisation_details(icb_practices_search_params)

    def _fetch_organisation_details(self, params):
        response = self._ods_client.fetch_organisation_data(params)
        return [
            OrganisationDetails(name=organisation["Name"], ods_code=organisation["OrgId"])
            for organisation in response
        ]
