from prmods.domain.ods_portal.models import CcgDetails
from prmods.domain.ods_portal.sources import construct_ccg_metadata_from_ods_portal_response
from tests.builders.ods_portal import build_ods_organisation_data_response


def test_returns_single_ccg():
    response_ccg_data = [build_ods_organisation_data_response(name="CCG", org_id="12C")]

    expected_ccgs = [CcgDetails(ods_code="12C", name="CCG")]

    actual = construct_ccg_metadata_from_ods_portal_response(response_ccg_data)

    assert actual == expected_ccgs


def test_returns_multiple_ccgs():
    response_ccg_data = [
        build_ods_organisation_data_response(name="CCG", org_id="12A"),
        build_ods_organisation_data_response(name="CCG 2", org_id="34A"),
        build_ods_organisation_data_response(name="CCG 3", org_id="56A"),
    ]

    expected_ccgs = [
        CcgDetails(ods_code="12A", name="CCG"),
        CcgDetails(ods_code="34A", name="CCG 2"),
        CcgDetails(ods_code="56A", name="CCG 3"),
    ]

    actual = construct_ccg_metadata_from_ods_portal_response(response_ccg_data)

    assert actual == expected_ccgs


def test_returns_unique_ccgs():
    response_ccg_data = [
        build_ods_organisation_data_response(name="CCG", org_id="12A"),
        build_ods_organisation_data_response(name="Another CCG", org_id="12A"),
    ]

    actual = construct_ccg_metadata_from_ods_portal_response(response_ccg_data)

    assert len(actual) == 1
