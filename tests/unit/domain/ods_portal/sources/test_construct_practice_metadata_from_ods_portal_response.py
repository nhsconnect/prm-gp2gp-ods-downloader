import pytest

from prmods.domain.ods_portal.models import PracticeDetails
from prmods.domain.ods_portal.sources import construct_practice_metadata_from_ods_portal_response
from tests.builders.ods_portal import build_ods_organisation_data_response


def test_returns_single_practice():
    response_practice_data = [
        build_ods_organisation_data_response(name="GP Practice", org_id="A12345")
    ]

    expected_practices = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice")
    ]

    asid_to_ods_mapping = {"A12345": ["123456781234"]}

    actual = construct_practice_metadata_from_ods_portal_response(
        response_practice_data, asid_to_ods_mapping
    )

    assert actual == expected_practices


def test_returns_multiple_practices():
    response_practice_data = [
        build_ods_organisation_data_response(name="GP Practice", org_id="A12345"),
        build_ods_organisation_data_response(name="GP Practice 2", org_id="B56789"),
        build_ods_organisation_data_response(name="GP Practice 3", org_id="C56789"),
    ]

    asid_to_ods_mapping = {
        "A12345": ["123456781234"],
        "B56789": ["443456781234"],
        "C56789": ["773456781234"],
    }

    expected_practices = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice"),
        PracticeDetails(asids=["443456781234"], ods_code="B56789", name="GP Practice 2"),
        PracticeDetails(asids=["773456781234"], ods_code="C56789", name="GP Practice 3"),
    ]

    actual = construct_practice_metadata_from_ods_portal_response(
        response_practice_data, asid_to_ods_mapping
    )

    assert actual == expected_practices


def test_returns_unique_practices():
    response_practice_data = [
        build_ods_organisation_data_response(name="GP Practice", org_id="A12345"),
        build_ods_organisation_data_response(name="Another GP Practice", org_id="A12345"),
    ]

    asid_to_ods_mapping = {"A12345": "123456781234"}

    actual = construct_practice_metadata_from_ods_portal_response(
        response_practice_data, asid_to_ods_mapping
    )

    assert len(actual) == 1


def test_skips_practice_and_warns_when_ods_not_in_asid_mapping():
    response_practice_data = [
        build_ods_organisation_data_response(name="GP Practice", org_id="A12345"),
        build_ods_organisation_data_response(name="Another GP Practice", org_id="B12345"),
    ]

    asid_to_ods_mapping = {"A12345": ["123456781234"]}

    expected_practices = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice"),
    ]

    with pytest.warns(RuntimeWarning):
        actual = construct_practice_metadata_from_ods_portal_response(
            response_practice_data, asid_to_ods_mapping
        )

    assert actual == expected_practices


def test_returns_single_practice_with_multiple_asids():
    response_practice_data = [
        build_ods_organisation_data_response(name="GP Practice", org_id="A12345")
    ]

    expected_practices = [
        PracticeDetails(
            asids=["123456781234", "654321234564"], ods_code="A12345", name="GP Practice"
        )
    ]

    asid_to_ods_mapping = {"A12345": ["123456781234", "654321234564"]}

    actual = construct_practice_metadata_from_ods_portal_response(
        response_practice_data, asid_to_ods_mapping
    )

    assert actual == expected_practices
