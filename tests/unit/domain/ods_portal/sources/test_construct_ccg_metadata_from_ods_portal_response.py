from unittest.mock import MagicMock

from prmods.domain.ods_portal.models import CcgDetails
from prmods.domain.ods_portal.sources import (
    construct_ccg_metadata_from_ods_portal_response,
    OdsDataFetcher,
)
from tests.builders.ods_portal import build_ods_organisation_data_response, build_mock_response

mock_response = build_mock_response(content=b'{"Organisations": []}')


def test_returns_single_ccg():
    mock_client = MagicMock()
    mock_client.get.side_effect = [mock_response]
    data_fetcher = OdsDataFetcher(mock_client, search_url="https://test.com/")

    response_ccg_data = [build_ods_organisation_data_response(name="CCG", org_id="12C")]

    expected_ccgs = [CcgDetails(ods_code="12C", name="CCG", practices=[])]

    actual = construct_ccg_metadata_from_ods_portal_response(response_ccg_data, data_fetcher)

    assert actual == expected_ccgs


def test_returns_unique_ccgs():
    mock_client = MagicMock()
    mock_client.get.side_effect = [mock_response]
    data_fetcher = OdsDataFetcher(mock_client, search_url="https://test.com/")

    response_ccg_data = [
        build_ods_organisation_data_response(name="CCG", org_id="12A"),
        build_ods_organisation_data_response(name="Another CCG", org_id="12A"),
    ]

    actual = construct_ccg_metadata_from_ods_portal_response(response_ccg_data, data_fetcher)

    assert len(actual) == 1


def test_returns_practice_ods_code_for_a_ccg():
    mock_client = MagicMock()
    mock_response_with_practice = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice", "OrgId": "A12345"}]}'
    )
    mock_client.get.side_effect = [mock_response_with_practice]

    data_fetcher = OdsDataFetcher(mock_client, search_url="https://test.com/")

    response_ccg_data = [
        build_ods_organisation_data_response(name="CCG", org_id="12A"),
    ]

    actual = construct_ccg_metadata_from_ods_portal_response(response_ccg_data, data_fetcher)

    assert actual[0].practices == ["A12345"]


def test_returns_multiple_ccgs_with_multiple_practices():
    mock_client = MagicMock()
    mock_response_1 = build_mock_response(content=b'{"Organisations": []}')
    mock_response_2 = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice 3", "OrgId": "C45678"}]}'
    )
    mock_response_3 = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice 4", "OrgId": "D34567"}, '
        b'{"Name": "GP Practice 5", "OrgId": "E98765"}, '
        b'{"Name": "GP Practice 6", "OrgId": "F23456"}]}'
    )
    mock_client.get.side_effect = [mock_response_1, mock_response_2, mock_response_3]
    data_fetcher = OdsDataFetcher(mock_client, search_url="https://test.com/")

    response_ccg_data = [
        build_ods_organisation_data_response(name="CCG", org_id="12A"),
        build_ods_organisation_data_response(name="CCG 2", org_id="34A"),
        build_ods_organisation_data_response(name="CCG 3", org_id="56A"),
    ]

    expected_ccgs = [
        CcgDetails(ods_code="12A", name="CCG", practices=[]),
        CcgDetails(ods_code="34A", name="CCG 2", practices=["C45678"]),
        CcgDetails(ods_code="56A", name="CCG 3", practices=["D34567", "E98765", "F23456"]),
    ]

    actual = construct_ccg_metadata_from_ods_portal_response(response_ccg_data, data_fetcher)

    assert actual == expected_ccgs
    assert mock_client.get.call_count == 3
