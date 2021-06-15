from _warnings import warn
from collections import defaultdict
from typing import List, Iterable, DefaultDict


class AsidLookup:
    def __init__(self, raw_asid_lookup: Iterable[dict]):
        self.ods_asid_mapping = self._construct_ods_asid_mapping(raw_asid_lookup)

    def _construct_ods_asid_mapping(self, raw_asid_lookup: Iterable[dict]) -> defaultdict:
        complete_mapping: DefaultDict[str, List[str]] = defaultdict(list)
        for mapping in raw_asid_lookup:
            complete_mapping[mapping["NACS"]].append(mapping["ASID"])
        return complete_mapping

    def is_ods_in_mapping(self, ods_code: str):
        if ods_code in self.ods_asid_mapping:
            return True
        else:
            warn(f"ODS code not found in ASID mapping: {ods_code}", RuntimeWarning)
            return False
