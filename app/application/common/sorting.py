from dataclasses import dataclass


@dataclass(frozen=True)
class SortOptions:
    field: str
    descending: bool = False
