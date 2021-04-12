import csv
import gzip
from typing import Iterable


def read_gzip_csv_file(file_content) -> Iterable[dict]:
    with gzip.open(file_content, mode="rt") as f:
        input_csv = csv.DictReader(f)
        yield from input_csv
