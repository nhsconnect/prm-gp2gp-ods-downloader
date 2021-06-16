from unittest.mock import MagicMock

import pytest

from prmods.domain.ods_portal.asid_lookup import AsidLookup, OdsAsid
from prmods.domain.ods_portal.ods_portal_client import OdsPortalClient
from prmods.domain.ods_portal.organisation_metadata import PracticeDetails, PracticeDetailsList
from tests.builders.ods_portal import build_mock_response


def test_returns_single_practice():
    mock_http_client = MagicMock()
    mock_practice_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice", "OrgId": "A12345"}]}'
    )
    mock_http_client.get.side_effect = [mock_practice_response]

    asid_lookup = AsidLookup([OdsAsid(ods_code="A12345", asid="123456781234")])

    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    expected_practices = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice")
    ]

    actual = PracticeDetailsList().create_practice_metadata_from_ods_portal_response(
        ods_client=ods_client, asid_lookup=asid_lookup
    )

    assert actual == expected_practices


def test_returns_multiple_practices():
    mock_http_client = MagicMock()
    mock_practice_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice", "OrgId": "A12345"}, '
        b'{"Name": "GP Practice 2", "OrgId": "B56789"}, '
        b'{"Name": "GP Practice 3", "OrgId": "C56789"}]}'
    )
    mock_http_client.get.side_effect = [mock_practice_response]

    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="A12345", asid="123456781234"),
            OdsAsid(ods_code="B56789", asid="443456781234"),
            OdsAsid(ods_code="C56789", asid="773456781234"),
        ]
    )
    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    expected_practices = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice"),
        PracticeDetails(asids=["443456781234"], ods_code="B56789", name="GP Practice 2"),
        PracticeDetails(asids=["773456781234"], ods_code="C56789", name="GP Practice 3"),
    ]

    actual = PracticeDetailsList().create_practice_metadata_from_ods_portal_response(
        ods_client=ods_client, asid_lookup=asid_lookup
    )

    assert actual == expected_practices


def test_returns_unique_practices():
    mock_http_client = MagicMock()
    mock_practice_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice", "OrgId": "A12345"}, '
        b'{"Name": "Another Practice 2", "OrgId": "A12345"}]}'
    )
    mock_http_client.get.side_effect = [mock_practice_response]

    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="A12345", asid="123456781234"),
        ]
    )

    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    actual = PracticeDetailsList().create_practice_metadata_from_ods_portal_response(
        ods_client=ods_client, asid_lookup=asid_lookup
    )

    assert len(actual) == 1


def test_skips_practice_and_warns_when_ods_not_in_asid_mapping():
    mock_http_client = MagicMock()
    mock_practice_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice", "OrgId": "A12345"}, '
        b'{"Name": "GP Practice 2", "OrgId": "B12345"}]}'
    )
    mock_http_client.get.side_effect = [mock_practice_response]

    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="A12345", asid="123456781234"),
        ]
    )
    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    expected_practices = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice"),
    ]

    with pytest.warns(RuntimeWarning):
        actual = PracticeDetailsList().create_practice_metadata_from_ods_portal_response(
            ods_client=ods_client, asid_lookup=asid_lookup
        )

    assert actual == expected_practices


def test_returns_single_practice_with_multiple_asids():
    mock_http_client = MagicMock()
    mock_practice_response = build_mock_response(
        content=b'{"Organisations": [{"Name": "GP Practice", "OrgId": "A12345"}]}'
    )
    mock_http_client.get.side_effect = [mock_practice_response]

    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="A12345", asid="123456781234"),
            OdsAsid(ods_code="A12345", asid="654321234564"),
        ]
    )
    ods_client = OdsPortalClient(mock_http_client, search_url="https://test.com/")

    expected_practices = [
        PracticeDetails(
            asids=["123456781234", "654321234564"], ods_code="A12345", name="GP Practice"
        )
    ]

    actual = PracticeDetailsList().create_practice_metadata_from_ods_portal_response(
        ods_client=ods_client, asid_lookup=asid_lookup
    )

    assert actual == expected_practices
