from dataclasses import dataclass
from typing import Iterable, List
from unittest.mock import Mock

from prmods.domain.ods_portal.asid_lookup import AsidLookup, OdsAsid
from prmods.domain.ods_portal.metadata_service import (
    Gp2gpOrganisationMetadataService,
    IcbDetails,
    PracticeDetails,
)
from prmods.domain.ods_portal.ods_portal_data_fetcher import OrganisationDetails


def test_calls_fetch_all_practices_with_toggle_param():
    # given
    mock_data_fetcher = Mock()
    mock_observability_probe = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(name="GP Practice", ods_code="A12345")
    ]
    asid_lookup = AsidLookup([OdsAsid("A12345", "123456789123")])

    metadata_service = Gp2gpOrganisationMetadataService(
        data_fetcher=mock_data_fetcher, observability_probe=mock_observability_probe
    )

    # when
    metadata_service.retrieve_practices_with_asids(
        asid_lookup=asid_lookup, show_prison_practices_toggle=True
    )

    # then
    mock_data_fetcher.fetch_all_practices.assert_called_with(show_prison_practices_toggle=True)


def test_returns_single_practice():
    mock_data_fetcher = Mock()
    mock_observability_probe = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(name="GP Practice", ods_code="A12345")
    ]

    metadata_service = Gp2gpOrganisationMetadataService(
        data_fetcher=mock_data_fetcher, observability_probe=mock_observability_probe
    )
    asid_lookup = AsidLookup([OdsAsid("A12345", "123456789123")])

    expected = [PracticeDetails(asids=["123456789123"], ods_code="A12345", name="GP Practice")]
    actual = metadata_service.retrieve_practices_with_asids(asid_lookup)

    assert actual == expected


def test_returns_multiple_practices():
    mock_data_fetcher = Mock()
    mock_observability_probe = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(ods_code="A12345", name="GP Practice"),
        OrganisationDetails(ods_code="B56789", name="GP Practice 2"),
        OrganisationDetails(ods_code="C56789", name="GP Practice 3"),
    ]

    metadata_service = Gp2gpOrganisationMetadataService(
        data_fetcher=mock_data_fetcher, observability_probe=mock_observability_probe
    )
    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="A12345", asid="123456781234"),
            OdsAsid(ods_code="B56789", asid="443456781234"),
            OdsAsid(ods_code="C56789", asid="773456781234"),
        ]
    )

    expected = [
        PracticeDetails(asids=["123456781234"], ods_code="A12345", name="GP Practice"),
        PracticeDetails(asids=["443456781234"], ods_code="B56789", name="GP Practice 2"),
        PracticeDetails(asids=["773456781234"], ods_code="C56789", name="GP Practice 3"),
    ]
    actual = metadata_service.retrieve_practices_with_asids(asid_lookup)

    assert actual == expected


def test_returns_single_practice_with_multiple_asids():
    mock_data_fetcher = Mock()
    mock_observability_probe = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(name="GP Practice", ods_code="A12345")
    ]

    metadata_service = Gp2gpOrganisationMetadataService(
        data_fetcher=mock_data_fetcher, observability_probe=mock_observability_probe
    )
    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="A12345", asid="123456781234"),
            OdsAsid(ods_code="A12345", asid="654321234564"),
        ]
    )

    expected = [
        PracticeDetails(
            asids=["123456781234", "654321234564"], ods_code="A12345", name="GP Practice"
        )
    ]
    actual = metadata_service.retrieve_practices_with_asids(asid_lookup)

    assert actual == expected


def test_skips_practice_and_warns_when_ods_not_in_asid_mapping():
    mock_data_fetcher = Mock()
    mock_observability_probe = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(ods_code="A12345", name="GP Practice"),
        OrganisationDetails(ods_code="B12345", name="GP Practice 2"),
    ]

    metadata_service = Gp2gpOrganisationMetadataService(
        data_fetcher=mock_data_fetcher, observability_probe=mock_observability_probe
    )

    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="B12345", asid="123456781234"),
        ]
    )

    expected = [PracticeDetails(asids=["123456781234"], ods_code="B12345", name="GP Practice 2")]

    actual = metadata_service.retrieve_practices_with_asids(asid_lookup)

    mock_observability_probe.record_asids_not_found.assert_called_once_with("A12345")

    assert actual == expected


def test_returns_unique_practices():
    mock_data_fetcher = Mock()
    mock_observability_probe = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(name="GP Practice", ods_code="A12345"),
        OrganisationDetails(name="GP Practice 2", ods_code="A12345"),
    ]

    metadata_service = Gp2gpOrganisationMetadataService(
        data_fetcher=mock_data_fetcher, observability_probe=mock_observability_probe
    )
    asid_lookup = AsidLookup([OdsAsid("A12345", "123456789123")])

    expected = [PracticeDetails(asids=["123456789123"], ods_code="A12345", name="GP Practice")]

    actual = metadata_service.retrieve_practices_with_asids(asid_lookup)

    mock_observability_probe.record_duplicate_organisation.assert_called_once_with("A12345")

    assert actual == expected


@dataclass
class ICBPracticeAllocation:
    icb: OrganisationDetails
    practices: List[OrganisationDetails]


class FakeDataFetcher:
    def __init__(self, icbs: Iterable[ICBPracticeAllocation]):
        self._icbs = [allocation.icb for allocation in icbs]
        self._practices = [practice for icb in icbs for practice in icb.practices]
        self._practices_by_icb_ods = {
            allocation.icb.ods_code: allocation.practices for allocation in icbs
        }

    def fetch_all_practices(self, show_prison_practices_toggle=False):
        return self._practices

    def fetch_all_icbs(self) -> List[OrganisationDetails]:
        return self._icbs

    def fetch_practices_for_icb(self, icb_ods_code: str) -> List[OrganisationDetails]:
        return self._practices_by_icb_ods[icb_ods_code]


def test_returns_single_icb_with_one_practice():
    mock_observability_probe = Mock()
    fake_data_fetcher = FakeDataFetcher(
        icbs=[
            ICBPracticeAllocation(
                icb=OrganisationDetails(ods_code="X12", name="ICB"),
                practices=[OrganisationDetails(ods_code="A12345", name="GP Practice")],
            )
        ]
    )
    canonical_practice_list = [
        PracticeDetails(name="GP Practice", ods_code="A12345", asids=["123456789123"])
    ]

    metadata_service = Gp2gpOrganisationMetadataService(fake_data_fetcher, mock_observability_probe)

    expected = [IcbDetails(ods_code="X12", name="ICB", practices=["A12345"])]

    actual = metadata_service.retrieve_icb_practice_allocations(
        canonical_practice_list=canonical_practice_list
    )

    assert actual == expected


def test_returns_multiple_icbs_with_at_least_one_practice():
    mock_observability_probe = Mock()
    fake_data_fetcher = FakeDataFetcher(
        icbs=[
            ICBPracticeAllocation(
                icb=OrganisationDetails(ods_code="12A", name="ICB"),
                practices=[],
            ),
            ICBPracticeAllocation(
                icb=OrganisationDetails(ods_code="34A", name="ICB 2"),
                practices=[OrganisationDetails(ods_code="C45678", name="GP Practice")],
            ),
            ICBPracticeAllocation(
                icb=OrganisationDetails(ods_code="56A", name="ICB 3"),
                practices=[
                    OrganisationDetails(ods_code="D34567", name="GP Practice 2"),
                    OrganisationDetails(ods_code="E98765", name="GP Practice 3"),
                    OrganisationDetails(ods_code="F23456", name="GP Practice 4"),
                ],
            ),
        ]
    )
    canonical_practice_list = [
        PracticeDetails(name="GP Practice", ods_code="C45678", asids=["123456789123"]),
        PracticeDetails(name="GP Practice 2", ods_code="D34567", asids=["223456789123"]),
        PracticeDetails(name="GP Practice 3", ods_code="E98765", asids=["323456789123"]),
        PracticeDetails(name="GP Practice 4", ods_code="F23456", asids=["423456789123"]),
    ]

    metadata_service = Gp2gpOrganisationMetadataService(fake_data_fetcher, mock_observability_probe)

    expected = [
        IcbDetails(ods_code="34A", name="ICB 2", practices=["C45678"]),
        IcbDetails(ods_code="56A", name="ICB 3", practices=["D34567", "E98765", "F23456"]),
    ]

    actual = metadata_service.retrieve_icb_practice_allocations(
        canonical_practice_list=canonical_practice_list
    )

    assert actual == expected


def test_returns_unique_icbs():
    mock_observability_probe = Mock()
    fake_data_fetcher = FakeDataFetcher(
        icbs=[
            ICBPracticeAllocation(
                icb=OrganisationDetails(ods_code="X12", name="ICB"),
                practices=[OrganisationDetails(ods_code="A12345", name="GP Practice")],
            ),
            ICBPracticeAllocation(
                icb=OrganisationDetails(ods_code="X12", name="Another ICB"),
                practices=[OrganisationDetails(ods_code="A12345", name="GP Practice")],
            ),
        ]
    )
    canonical_practice_list = [
        PracticeDetails(name="GP Practice", ods_code="A12345", asids=["123456789123"])
    ]

    metadata_service = Gp2gpOrganisationMetadataService(fake_data_fetcher, mock_observability_probe)

    expected = [IcbDetails(ods_code="X12", name="ICB", practices=["A12345"])]

    actual = metadata_service.retrieve_icb_practice_allocations(canonical_practice_list)

    mock_observability_probe.record_duplicate_organisation.assert_called_once_with("X12")

    assert actual == expected


def test_filters_out_icb_practice_that_are_not_in_the_canonical_list():
    mock_observability_probe = Mock()
    fake_data_fetcher = FakeDataFetcher(
        icbs=[
            ICBPracticeAllocation(
                icb=OrganisationDetails(ods_code="X12", name="ICB"),
                practices=[
                    OrganisationDetails(ods_code="A12345", name="GP Practice"),
                    OrganisationDetails(ods_code="A12346", name="Other Practice"),
                ],
            )
        ]
    )
    canonical_practice_list = [
        PracticeDetails(ods_code="A12345", name="GP Practice", asids=["123456781234"])
    ]

    metadata_service = Gp2gpOrganisationMetadataService(fake_data_fetcher, mock_observability_probe)

    expected = [IcbDetails(ods_code="X12", name="ICB", practices=["A12345"])]

    actual = metadata_service.retrieve_icb_practice_allocations(
        canonical_practice_list=canonical_practice_list
    )

    assert actual == expected
