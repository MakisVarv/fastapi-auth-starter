from app.application.common.sorting import SortOptions


def apply_sorting(
    statement,
    *,
    sort_columns,
    options: SortOptions,
    secondary_column,
):
    sort_column = sort_columns[options.field]

    order = sort_column.desc() if options.descending else sort_column.asc()

    statement = statement.order_by(order)
    if secondary_column is not sort_column:
        statement = statement.order_by(secondary_column.asc())

    return statement
