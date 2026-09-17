from app.application.common.sorting import SortOptions


def parse_sort(sort: str) -> SortOptions:
    descending = sort.startswith("-")
    field = sort[1:] if descending else sort

    return SortOptions(
        field=field,
        descending=descending,
    )
