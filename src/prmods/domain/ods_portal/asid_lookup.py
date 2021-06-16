from _warnings import warn
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Iterable, DefaultDict


@dataclass
class OdsAsid:
    ods_code: str
    asid: str


class AsidLookup:
    @classmethod
    def from_spine_directory_format(cls, rows: Iterable[dict]):
        return cls([OdsAsid(row["NACS"], row["ASID"]) for row in rows])

    def __init__(self, mappings: Iterable[OdsAsid]):
        self.ods_asid_mapping = _construct_ods_asid_mapping(mappings)

    def is_ods_in_mapping(self, ods_code: str):
        if ods_code in self.ods_asid_mapping:
            return True
        else:
            warn(f"ODS code not found in ASID mapping: {ods_code}", RuntimeWarning)
            return False


def _construct_ods_asid_mapping(mappings: Iterable[OdsAsid]) -> defaultdict:
    ods_asid_mapping: DefaultDict[str, List[str]] = defaultdict(list)
    for mapping in mappings:
        ods_asid_mapping[mapping.ods_code].append(mapping.asid)
    return ods_asid_mapping
