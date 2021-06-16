from unittest.mock import Mock

from prmods.domain.ods_portal.ods_portal_data_fetcher import (
    OdsPortalDataFetcher,
    OrganisationDetails,
)
from tests.builders.ods_portal import build_ods_organisation_data_response


def test_fetch_all_practices_returns_a_list_of_organisation_details():
    mock_ods_client = Mock()
    mock_ods_client.fetch_organisation_data.return_value = [
        build_ods_organisation_data_response(name="GP Practice", org_id="A12345"),
        build_ods_organisation_data_response(name="GP Practice 2", org_id="B12345"),
    ]

    ods_portal_data_fetcher = OdsPortalDataFetcher(ods_client=mock_ods_client)

    expected = [
        OrganisationDetails(name="GP Practice", ods_code="A12345"),
        OrganisationDetails(name="GP Practice 2", ods_code="B12345"),
    ]
    actual = ods_portal_data_fetcher.fetch_all_practices()

    assert actual == expected
    mock_ods_client.fetch_organisation_data.assert_called_once_with(
        {
            "PrimaryRoleId": "RO177",
            "Status": "Active",
            "NonPrimaryRoleId": "RO76",
            "Limit": "1000",
        }
    )
