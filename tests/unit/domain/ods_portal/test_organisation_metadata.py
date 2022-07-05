from datetime import datetime

from dateutil.tz import tzutc
from freezegun import freeze_time

from prmods.domain.ods_portal.metadata_service import (
    IcbDetails,
    OrganisationMetadata,
    PracticeDetails,
)


@freeze_time(datetime(year=2019, month=6, day=2, hour=23, second=42), tz_offset=0)
def test_has_correct_generated_on_timestamp_given_time():
    expected_generated_on = datetime(year=2019, month=6, day=2, hour=23, second=42, tzinfo=tzutc())

    actual = OrganisationMetadata.from_practice_and_icb_lists(
        practices=[], icbs=[], year=2019, month=6
    )

    assert actual.generated_on == expected_generated_on


def test_returns_given_year_and_month():
    year = 2019
    month = 6
    actual = OrganisationMetadata.from_practice_and_icb_lists(
        practices=[], icbs=[], year=year, month=month
    )

    assert actual.year == year
    assert actual.month == month


def test_returns_multiple_practices_and_icbs():
    practice_metadata = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice"),
        PracticeDetails(asids=["443456781234"], ods_code="B56789", name="GP Practice 2"),
        PracticeDetails(asids=["773456781234"], ods_code="C56789", name="GP Practice 3"),
    ]

    icb_metadata = [
        IcbDetails(ods_code="12A", name="ICB", practices=[]),
        IcbDetails(ods_code="34A", name="ICB 2", practices=["A12345"]),
        IcbDetails(ods_code="56A", name="ICB 3", practices=["B56789", "C56789"]),
    ]

    actual = OrganisationMetadata.from_practice_and_icb_lists(
        practices=practice_metadata, icbs=icb_metadata, year=2019, month=6
    )

    assert actual.practices == practice_metadata
    assert actual.icbs == icb_metadata
