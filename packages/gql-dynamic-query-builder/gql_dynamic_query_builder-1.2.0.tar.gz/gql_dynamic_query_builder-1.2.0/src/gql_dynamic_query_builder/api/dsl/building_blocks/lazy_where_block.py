from __future__ import annotations

from gql_dynamic_query_builder.api.dsl.building_blocks.helpers import LAZY_WHERE_INFO


class LazyWhereBlock:

    def __init__(self, field_name: str, is_optional: bool):
        self.field_name = field_name
        self.is_optional = is_optional

    def _eq(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_eq', self.is_optional

    def _neq(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_neq', self.is_optional

    def _gt(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_gt', self.is_optional

    def _gte(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_gte', self.is_optional

    def _lt(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_lt', self.is_optional

    def _lte(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_lte', self.is_optional

    def _in(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_in', self.is_optional

    def _nin(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_nin', self.is_optional

    def _is_null(self, value: str | float | int) -> LAZY_WHERE_INFO:
        return self.field_name, value, '_is_null', self.is_optional
