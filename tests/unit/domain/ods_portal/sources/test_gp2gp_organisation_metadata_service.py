from unittest.mock import Mock

from prmods.domain.ods_portal.asid_lookup import AsidLookup, OdsAsid
from prmods.domain.ods_portal.gp2gp_organisation_metadata_service import (
    Gp2gpOrganisationMetadataService,
)
from prmods.domain.ods_portal.ods_portal_data_fetcher import OrganisationDetails
from prmods.domain.ods_portal.organisation_metadata import PracticeDetails


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
