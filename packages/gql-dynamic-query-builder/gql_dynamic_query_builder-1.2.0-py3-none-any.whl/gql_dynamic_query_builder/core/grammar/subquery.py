from pyparsing import (
    Keyword,
    Literal,
    OneOrMore,
    Optional,
    ParserElement,
    QuotedString,
    Word,
    ZeroOrMore,
    alphanums,
    alphas,
    original_text_for,
)

from gql_dynamic_query_builder.core.grammar.where_clause import WHERE_CLAUSE

SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE = (
    ~Keyword('where')
    + Word(alphas + '_')
    + Literal(':')
    + (Word(alphanums) | QuotedString('"'))
    + Optional(Literal(','))
)

PRECEDING_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE = Literal('(') + original_text_for(
    ZeroOrMore(SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE.copy())
)

FOLLOWING_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE = original_text_for(
    ZeroOrMore(SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE.copy())
) + Literal(')')

PARENTHESES_AND_ONE_OR_MORE_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE = (
    Literal('(') + SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE.copy() + Literal(')')
)

WHERE_CLAUSE_WRAPPED_IN_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE = (
    PRECEDING_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE.copy()
    + WHERE_CLAUSE.copy()
    + FOLLOWING_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE.copy()
)

GENERIC_SUBQUERY_BODY = Literal('{') + OneOrMore(Word(alphanums + '_')) + Literal('}')

GENERIC_SUBQUERY = (
    Word(alphas + '_')
    + Optional(
        WHERE_CLAUSE_WRAPPED_IN_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE
        | PARENTHESES_AND_ONE_OR_MORE_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE
    )
    + GENERIC_SUBQUERY_BODY.copy()
)


def get_table_specific_subquery(
    table_name: str,
    where_clause: ParserElement,
    filter_parameters_except_where: ParserElement,
    no_filters: ParserElement,
) -> ParserElement:
    return (
        Literal(table_name)
        + (
            (
                PRECEDING_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE.copy()
                + where_clause
                + filter_parameters_except_where
                + FOLLOWING_SUBQUERY_FILTERS_EXCLUDING_WHERE_CLAUSE.copy()
            )
            | no_filters
        )
        + GENERIC_SUBQUERY_BODY.copy()
    )
