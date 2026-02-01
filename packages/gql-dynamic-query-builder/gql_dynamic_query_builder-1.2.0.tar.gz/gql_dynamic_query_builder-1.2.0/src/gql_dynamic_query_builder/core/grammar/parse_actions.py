### These functions are used as parse actions for matches
from pyparsing import ParseResults


def extend_where_clauses(
    existing_where_clause: ParseResults, where_clauses: str
) -> str:
    if where_clauses:
        return f' {"".join(existing_where_clause)} {where_clauses} '
    else:
        return f' {"".join(existing_where_clause)}'


def inject_new_where_clauses(where_clauses: str) -> str:
    return f' where: {{{where_clauses}}} ' if where_clauses else ''


def create_filter_section_with_clauses(
    where_clauses: str, other_filter_params: str
) -> str:
    if where_clauses:
        if other_filter_params:
            return f'(where: {{{where_clauses}}} {other_filter_params})'
        else:
            return f'(where: {{{where_clauses}}})'
    elif other_filter_params:
        return f' ({other_filter_params}) '
    else:
        return ''


def inject_other_filter_clauses(other_filter_params: str) -> str:
    return ''.join(other_filter_params) if other_filter_params else ''
