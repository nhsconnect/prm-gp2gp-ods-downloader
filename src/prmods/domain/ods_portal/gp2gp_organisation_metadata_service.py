from typing import List

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.ods_portal_data_fetcher import OdsPortalDataFetcher
from prmods.domain.ods_portal.organisation_metadata import PracticeDetails


class Gp2gpOrganisationMetadataService:
    def __init__(self, data_fetcher: OdsPortalDataFetcher):
        self._data_fetcher = data_fetcher

    def retrieve_practices_with_asids(self, asid_lookup: AsidLookup) -> List[PracticeDetails]:
        practices = self._data_fetcher.fetch_all_practices()

        return [
            PracticeDetails(
                asids=asid_lookup.get_asids(practice.ods_code),
                ods_code=practice.ods_code,
                name=practice.name,
            )
            for practice in practices
            if asid_lookup.has_ods(practice.ods_code)
        ]
