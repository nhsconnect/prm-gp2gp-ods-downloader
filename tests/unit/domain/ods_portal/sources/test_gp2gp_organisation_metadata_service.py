from dataclasses import dataclass
from typing import List, Iterable
from unittest.mock import Mock

import pytest

from prmods.domain.ods_portal.asid_lookup import AsidLookup, OdsAsid
from prmods.domain.ods_portal.metadata_service import (
    Gp2gpOrganisationMetadataService,
)
from prmods.domain.ods_portal.ods_portal_data_fetcher import OrganisationDetails
from prmods.domain.ods_portal.organisation_metadata import PracticeDetails, CcgDetails


def test_returns_single_practice():
    mock_data_fetcher = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(name="GP Practice", ods_code="A12345")
    ]

    metadata_service = Gp2gpOrganisationMetadataService(data_fetcher=mock_data_fetcher)
    asid_lookup = AsidLookup([OdsAsid("A12345", "123456789123")])

    expected = [PracticeDetails(asids=["123456789123"], ods_code="A12345", name="GP Practice")]
    actual = metadata_service.retrieve_practices_with_asids(asid_lookup)

    assert actual == expected


def test_returns_multiple_practices():
    mock_data_fetcher = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(ods_code="A12345", name="GP Practice"),
        OrganisationDetails(ods_code="B56789", name="GP Practice 2"),
        OrganisationDetails(ods_code="C56789", name="GP Practice 3"),
    ]

    metadata_service = Gp2gpOrganisationMetadataService(data_fetcher=mock_data_fetcher)
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
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(name="GP Practice", ods_code="A12345")
    ]

    metadata_service = Gp2gpOrganisationMetadataService(data_fetcher=mock_data_fetcher)
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
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(ods_code="A12345", name="GP Practice"),
        OrganisationDetails(ods_code="B12345", name="GP Practice 2"),
    ]

    metadata_service = Gp2gpOrganisationMetadataService(data_fetcher=mock_data_fetcher)
    asid_lookup = AsidLookup(
        [
            OdsAsid(ods_code="B12345", asid="123456781234"),
        ]
    )

    expected = [PracticeDetails(asids=["123456781234"], ods_code="B12345", name="GP Practice 2")]

    with pytest.warns(RuntimeWarning):
        actual = metadata_service.retrieve_practices_with_asids(asid_lookup)

    assert actual == expected


def test_returns_unique_practices():
    mock_data_fetcher = Mock()
    mock_data_fetcher.fetch_all_practices.return_value = [
        OrganisationDetails(name="GP Practice", ods_code="A12345"),
        OrganisationDetails(name="GP Practice 2", ods_code="A12345"),
    ]

    metadata_service = Gp2gpOrganisationMetadataService(data_fetcher=mock_data_fetcher)
    asid_lookup = AsidLookup([OdsAsid("A12345", "123456789123")])

    expected = [PracticeDetails(asids=["123456789123"], ods_code="A12345", name="GP Practice")]
    actual = metadata_service.retrieve_practices_with_asids(asid_lookup)

    assert actual == expected


@dataclass
class CCGPracticeAllocation:
    ccg: OrganisationDetails
    practices: List[OrganisationDetails]


class FakeDataFetcher:
    def __init__(self, ccgs: Iterable[CCGPracticeAllocation]):
        self._ccgs = [allocation.ccg for allocation in ccgs]
        self._practices_by_ccg_ods = {
            allocation.ccg.ods_code: allocation.practices for allocation in ccgs
        }

    def fetch_all_ccgs(self) -> List[OrganisationDetails]:
        return self._ccgs

    def fetch_practices_for_ccg(self, ccg_ods_code: str) -> List[OrganisationDetails]:
        return self._practices_by_ccg_ods[ccg_ods_code]


def test_returns_single_ccg_with_one_practice():

    fake_data_fetcher = FakeDataFetcher(
        ccgs=[
            CCGPracticeAllocation(
                ccg=OrganisationDetails(ods_code="X12", name="CCG"),
                practices=[OrganisationDetails(ods_code="A12345", name="GP Practice")],
            )
        ]
    )

    metadata_service = Gp2gpOrganisationMetadataService(fake_data_fetcher)

    expected = [CcgDetails(ods_code="X12", name="CCG", practices=["A12345"])]

    actual = metadata_service.retrieve_ccg_practice_allocations()

    assert actual == expected
