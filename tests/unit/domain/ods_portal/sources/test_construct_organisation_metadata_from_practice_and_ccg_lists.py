from datetime import datetime
from unittest.mock import Mock

from dateutil.tz import tzutc
from freezegun import freeze_time

from prmods.domain.ods_portal.asid_lookup import AsidLookup, OdsAsid
from prmods.domain.ods_portal.organisation_metadata import CcgDetails, PracticeDetails
from prmods.domain.ods_portal.organisation_metadata import OrganisationMetadataConstructor
from tests.builders.ods_portal import build_ods_organisation_data_response


@freeze_time(datetime(year=2019, month=6, day=2, hour=23, second=42), tz_offset=0)
def test_has_correct_generated_on_timestamp_given_time():
    expected_generated_on = datetime(year=2019, month=6, day=2, hour=23, second=42, tzinfo=tzutc())

    mock_asid_lookup = Mock()
    mock_ods_client = Mock()
    mock_ods_client.fetch_organisation_data.return_value = []

    org_metadata_constructor = OrganisationMetadataConstructor(mock_ods_client, mock_asid_lookup)
    actual = org_metadata_constructor.create_organisation_metadata_from_practice_and_ccg_lists()

    assert actual.generated_on == expected_generated_on


def test_returns_multiple_practices_and_ccgs():
    practice_metadata_response = [
        build_ods_organisation_data_response(
            org_id="A12345",
            name="GP Practice",
        ),
        build_ods_organisation_data_response(
            org_id="B56789",
            name="GP Practice 2",
        ),
        build_ods_organisation_data_response(
            org_id="C56789",
            name="GP Practice 3",
        ),
    ]

    ccg_metadata_response = [
        build_ods_organisation_data_response(org_id="12A", name="CCG"),
        build_ods_organisation_data_response(org_id="34A", name="CCG 2"),
        build_ods_organisation_data_response(org_id="56A", name="CCG 3"),
    ]

    expected_practice_metadata = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice"),
        PracticeDetails(asids=["443456781234"], ods_code="B56789", name="GP Practice 2"),
        PracticeDetails(asids=["773456781234"], ods_code="C56789", name="GP Practice 3"),
    ]

    expected_ccg_metadata = [
        CcgDetails(ods_code="12A", name="CCG", practices=[]),
        CcgDetails(ods_code="34A", name="CCG 2", practices=[]),
        CcgDetails(ods_code="56A", name="CCG 3", practices=[]),
    ]

    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="A12345", asid="123456781234"),
            OdsAsid(ods_code="B56789", asid="443456781234"),
            OdsAsid(ods_code="C56789", asid="773456781234"),
        ]
    )

    mock_ods_client = Mock()

    mock_ods_client.fetch_organisation_data.side_effect = [
        practice_metadata_response,
        ccg_metadata_response,
        [],
        [],
        [],
    ]

    org_metadata_constructor = OrganisationMetadataConstructor(mock_ods_client, asid_lookup)

    actual = org_metadata_constructor.create_organisation_metadata_from_practice_and_ccg_lists()

    assert actual.practices == expected_practice_metadata
    assert actual.ccgs == expected_ccg_metadata
