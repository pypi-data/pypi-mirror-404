from pyparsing import (
    Forward,
    Literal,
    ParserElement,
    QuotedString,
    Word,
    ZeroOrMore,
    alphas,
)

RECURSIVE_WHERE_CONDITION = Forward()

RECURSIVE_WHERE_VALUE = QuotedString(quote_char='"', unquote_results=False) | (
    Literal('{') + RECURSIVE_WHERE_CONDITION + Literal('}')
)

RECURSIVE_WHERE_CONDITION <<= Word(alphas + '_') + Literal(':') + RECURSIVE_WHERE_VALUE

WHERE_CLAUSE = (
    Literal('where')
    + Literal(':')
    + Literal('{')
    + ZeroOrMore(RECURSIVE_WHERE_CONDITION)
    + Literal('}')
)


def get_new_where_clause_and_content() -> tuple[ParserElement, ParserElement]:
    recursive_where_condition = RECURSIVE_WHERE_CONDITION.copy()
    where_clause = (
        Literal('where')
        + Literal(':')
        + Literal('{')
        + recursive_where_condition
        + Literal('}')
    )
    return where_clause, recursive_where_condition
