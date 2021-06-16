from unittest.mock import MagicMock

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.organisation_metadata import (
    CcgDetails,
    OrganisationMetadataConstructor,
)
from prmods.domain.ods_portal.ods_portal_client import OdsPortalClient
from tests.builders.ods_portal import build_mock_response


def test_returns_single_ccg():
    mock_http_client = MagicMock()
    mock_ccg_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "CCG", "OrgId": "12C"}]}'
    )
    mock_ccg_practice_response = build_mock_response(content=b'{"Organisations": []}')
    mock_http_client.get.side_effect = [mock_ccg_response, mock_ccg_practice_response]
    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    organisation_metadata_constructor = OrganisationMetadataConstructor(
        ods_client, asid_lookup=AsidLookup([])
    )

    expected_ccgs = [CcgDetails(ods_code="12C", name="CCG", practices=[])]

    actual = organisation_metadata_constructor.create_ccg_metadata_from_ods_portal_response()

    assert actual == expected_ccgs


def test_returns_unique_ccgs():
    mock_http_client = MagicMock()
    mock_ccg_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "CCG", "OrgId": "12A"},'
        b'{"Name": "Another CCG", "OrgId": "12A"}]}'
    )
    mock_ccg_practice_response = build_mock_response(content=b'{"Organisations": []}')
    mock_http_client.get.side_effect = [mock_ccg_response, mock_ccg_practice_response]
    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    organisation_metadata_constructor = OrganisationMetadataConstructor(
        ods_client, asid_lookup=AsidLookup([])
    )

    actual = organisation_metadata_constructor.create_ccg_metadata_from_ods_portal_response()

    assert len(actual) == 1


def test_returns_practice_ods_code_for_a_ccg():
    mock_http_client = MagicMock()
    mock_ccg_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "CCG", "OrgId": "12A"}]}'
    )
    mock_ccg_practice_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice", "OrgId": "A12345"}]}'
    )
    mock_http_client.get.side_effect = [mock_ccg_response, mock_ccg_practice_response]

    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    organisation_metadata_constructor = OrganisationMetadataConstructor(
        ods_client, asid_lookup=AsidLookup([])
    )

    actual = organisation_metadata_constructor.create_ccg_metadata_from_ods_portal_response()

    assert actual[0].practices == ["A12345"]


def test_returns_multiple_ccgs_with_multiple_practices():
    mock_http_client = MagicMock()
    mock_ccg_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "CCG", "OrgId": "12A"},'
        b'{"Name": "CCG 2", "OrgId": "34A"},'
        b'{"Name": "CCG 3", "OrgId": "56A"}]}'
    )
    mock_ccg_practice_response_1 = build_mock_response(content=b'{"Organisations": []}')
    mock_ccg_practice_response_2 = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice 3", "OrgId": "C45678"}]}'
    )
    mock_ccg_practice_response_3 = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice 4", "OrgId": "D34567"}, '
        b'{"Name": "GP Practice 5", "OrgId": "E98765"}, '
        b'{"Name": "GP Practice 6", "OrgId": "F23456"}]}'
    )
    mock_http_client.get.side_effect = [
        mock_ccg_response,
        mock_ccg_practice_response_1,
        mock_ccg_practice_response_2,
        mock_ccg_practice_response_3,
    ]
    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    organisation_metadata_constructor = OrganisationMetadataConstructor(
        ods_client, asid_lookup=AsidLookup([])
    )

    expected_ccgs = [
        CcgDetails(ods_code="12A", name="CCG", practices=[]),
        CcgDetails(ods_code="34A", name="CCG 2", practices=["C45678"]),
        CcgDetails(ods_code="56A", name="CCG 3", practices=["D34567", "E98765", "F23456"]),
    ]

    actual = organisation_metadata_constructor.create_ccg_metadata_from_ods_portal_response()

    assert actual == expected_ccgs
    assert mock_http_client.get.call_count == 4
