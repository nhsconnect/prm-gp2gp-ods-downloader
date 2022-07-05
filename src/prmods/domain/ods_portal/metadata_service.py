from dataclasses import dataclass
from datetime import datetime
from logging import Logger, getLogger
from typing import Iterable, List, Optional, Set

from dateutil.tz import tzutc

from prmods.domain.ods_portal.asid_lookup import AsidLookup
from prmods.domain.ods_portal.ods_portal_data_fetcher import OdsDataSource, OrganisationDetails


@dataclass
class IcbDetails:
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
    year: int
    month: int
    practices: List[PracticeDetails]
    icbs: List[IcbDetails]

    @classmethod
    def from_practice_and_icb_lists(
        cls, practices: List[PracticeDetails], icbs: List[IcbDetails], year: int, month: int
    ):
        return cls(
            generated_on=datetime.now(tzutc()),
            practices=practices,
            icbs=icbs,
            year=year,
            month=month,
        )


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

    def retrieve_practices_with_asids(
        self, asid_lookup: AsidLookup, show_prison_practices_toggle: Optional[bool] = False
    ) -> List[PracticeDetails]:
        practices = self._data_fetcher.fetch_all_practices(
            show_prison_practices_toggle=show_prison_practices_toggle
        )
        unique_practices = self._remove_duplicate_organisations(practices)

        return list(self._enrich_practices_with_asids(unique_practices, asid_lookup))

    def retrieve_icb_practice_allocations(
        self, canonical_practice_list: List[PracticeDetails]
    ) -> List[IcbDetails]:
        icbs = self._data_fetcher.fetch_all_icbs()
        unique_icbs = self._remove_duplicate_organisations(icbs)
        canonical_practice_ods_codes = {practice.ods_code for practice in canonical_practice_list}
        icb_practice_allocations = [
            self._fetch_icb_practice_allocation(icb, canonical_practice_ods_codes)
            for icb in unique_icbs
        ]
        icbs_containing_practices = [
            icb for icb in icb_practice_allocations if len(icb.practices) > 0
        ]
        return icbs_containing_practices

    def _fetch_icb_practice_allocation(
        self, icb: OrganisationDetails, canonical_practice_ods_codes: Set[str]
    ) -> IcbDetails:
        icb_practices = self._data_fetcher.fetch_practices_for_icb(icb.ods_code)

        return IcbDetails(
            ods_code=icb.ods_code,
            name=icb.name,
            practices=[
                practice.ods_code
                for practice in icb_practices
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
