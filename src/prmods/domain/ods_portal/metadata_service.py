from dataclasses import dataclass
from datetime import datetime
from logging import Logger, getLogger
from typing import Iterable, List, Set

from dateutil.tz import tzutc

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.ods_portal_data_fetcher import OdsDataSource, OrganisationDetails


@dataclass
class CcgDetails:
    ods_code: str
    name: str
    practices: List[str]


@dataclass
class PracticeDetails:
    ods_code: str
    name: str
    asids: List[str]


@dataclass
class OrganisationMetadata:
    generated_on: datetime
    practices: List[PracticeDetails]
    ccgs: List[CcgDetails]

    @classmethod
    def from_practice_and_ccg_lists(cls, practices: List[PracticeDetails], ccgs: List[CcgDetails]):
        return cls(generated_on=datetime.now(tzutc()), practices=practices, ccgs=ccgs)


module_logger = getLogger(__name__)


class MetadataServiceObservabilityProbe:
    def __init__(self, logger: Logger = module_logger):
        self._logger = logger

    def record_asids_not_found(self, ods_code: str):
        self._logger.warning(
            f"ASIDS not found for ODS code: {ods_code}",
            extra={"event": "ASIDS_NOT_FOUND", "ods_code": ods_code},
        )

    def record_duplicate_organisation(self, ods_code: str):
        self._logger.warning(
            f"Duplicate ODS code found: {ods_code}",
            extra={"event": "DUPLICATE_ODS_CODE_FOUND", "ods_code": ods_code},
        )


class Gp2gpOrganisationMetadataService:
    def __init__(
        self, data_fetcher: OdsDataSource, observability_probe: MetadataServiceObservabilityProbe
    ):
        self._data_fetcher = data_fetcher
        self._probe = observability_probe

    def retrieve_practices_with_asids(self, asid_lookup: AsidLookup) -> List[PracticeDetails]:
        practices = self._data_fetcher.fetch_all_practices()
        unique_practices = self._remove_duplicate_organisations(practices)

        return list(self._enrich_practices_with_asids(unique_practices, asid_lookup))

    def retrieve_ccg_practice_allocations(
        self, canonical_practice_list: List[PracticeDetails]
    ) -> List[CcgDetails]:
        ccgs = self._data_fetcher.fetch_all_ccgs()
        unique_ccgs = self._remove_duplicate_organisations(ccgs)
        canonical_practice_ods_codes = {practice.ods_code for practice in canonical_practice_list}
        ccg_practice_allocations = [
            self._fetch_ccg_practice_allocation(ccg, canonical_practice_ods_codes)
            for ccg in unique_ccgs
        ]
        ccgs_containing_practices = [
            ccg for ccg in ccg_practice_allocations if len(ccg.practices) > 0
        ]
        return ccgs_containing_practices

    def _fetch_ccg_practice_allocation(
        self, ccg: OrganisationDetails, canonical_practice_ods_codes: Set[str]
    ) -> CcgDetails:
        ccg_practices = self._data_fetcher.fetch_practices_for_ccg(ccg.ods_code)

        return CcgDetails(
            ods_code=ccg.ods_code,
            name=ccg.name,
            practices=[
                practice.ods_code
                for practice in ccg_practices
                if practice.ods_code in canonical_practice_ods_codes
            ],
        )

    def _enrich_practices_with_asids(
        self, practices: Iterable[OrganisationDetails], asid_lookup: AsidLookup
    ):
        for practice in practices:
            if asid_lookup.has_ods(practice.ods_code):
                yield PracticeDetails(
                    asids=asid_lookup.get_asids(practice.ods_code),
                    ods_code=practice.ods_code,
                    name=practice.name,
                )
            else:
                self._probe.record_asids_not_found(practice.ods_code)

    def _remove_duplicate_organisations(
        self,
        organisations: List[OrganisationDetails],
    ) -> Iterable[OrganisationDetails]:
        seen_ods = set()
        for organisation in organisations:
            if organisation.ods_code not in seen_ods:
                yield organisation
            else:
                self._probe.record_duplicate_organisation(organisation.ods_code)
            seen_ods.add(organisation.ods_code)
