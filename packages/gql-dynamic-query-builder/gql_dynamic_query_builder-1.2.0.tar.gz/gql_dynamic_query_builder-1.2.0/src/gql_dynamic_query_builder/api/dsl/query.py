from __future__ import annotations

from typing import Iterable

from gql_dynamic_query_builder.api.builder import GQLDynamicQueryBuilder
from gql_dynamic_query_builder.api.dsl.building_blocks.lazy_where_block import LazyWhereBlock
from gql_dynamic_query_builder.api.dsl.building_blocks.helpers import LAZY_WHERE_INFO, purge_where_info, \
    OrLazyWhereInfo, AndLazyWhereInfo
from gql_dynamic_query_builder.api.dsl.building_blocks.query_block import (
    QueryBuildingBlock,
)


def dynamic_query(query: str) -> QueryBuildingBlock:
    builder = GQLDynamicQueryBuilder(query)
    return QueryBuildingBlock(builder)


def _or(to_conjunct: Iterable[LAZY_WHERE_INFO | AndLazyWhereInfo | OrLazyWhereInfo]) -> OrLazyWhereInfo:
    purged_to_conjunct = purge_where_info(to_conjunct, OrLazyWhereInfo)
    return OrLazyWhereInfo(tuple(purged_to_conjunct))


def _and(to_conjunct: Iterable[LAZY_WHERE_INFO | AndLazyWhereInfo | OrLazyWhereInfo]) -> AndLazyWhereInfo:
    purged_to_conjunct = purge_where_info(to_conjunct, AndLazyWhereInfo)
    return AndLazyWhereInfo(tuple(purged_to_conjunct))


def where(field_name: str, is_optional: bool = False) -> LazyWhereBlock:
    return LazyWhereBlock(field_name, is_optional)
