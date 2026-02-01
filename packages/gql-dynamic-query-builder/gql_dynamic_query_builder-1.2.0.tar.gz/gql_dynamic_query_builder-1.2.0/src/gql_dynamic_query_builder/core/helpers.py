import json

ALLOWED_VALUES = str | float | int | list[str] | list[float] | list[int]


def construct_operation_value_string(value: str | int | list, operation: str) -> str:
    if operation in ['_like', '_ilike']:
        value = f'"%{value}%"'
    elif isinstance(value, str):
        value = f'"{value}"'

    return f'{operation}: {value}'


def construct_where_clause_string(nested_anc_explicit_where_clauses: dict) -> str:
    nested_field_clauses = []
    for key, value in nested_anc_explicit_where_clauses.items():
        if isinstance(value, dict):
            nested_field_clauses.append(
                f'{key}: {{{construct_where_clause_string(value)}}}'
            )
        else:
            nested_field_clauses.append(value)

    return ' '.join(nested_field_clauses)


def construct_filter_parameters_except_where_clause_string(
    limit: int | None, offset: int | None
) -> str:
    limit_clause = f'limit: {limit}' if limit else None

    offset_clause = f'offset: {offset}' if offset else None
    filter_params_except_where_clause_string = (
        f' {" ".join([c for c in [offset_clause, limit_clause] if c is not None])} '
    )
    return filter_params_except_where_clause_string


def recursive_dict_merge(dict_to_merge_into: dict, dict_to_merge: dict) -> dict:
    for k, v in dict_to_merge.items():
        if (
            k in dict_to_merge_into
            and isinstance(dict_to_merge_into[k], dict)
            and isinstance(v, dict)
        ):
            recursive_dict_merge(dict_to_merge_into[k], v)
        else:
            dict_to_merge_into[k] = v
    return dict_to_merge_into


def handle_skip_if_none(skip_if_none: bool, to_return=None):
    if skip_if_none:
        return to_return
    else:
        raise ValueError(
            'Encountered None value - '
            'if you want to skip it set skip_if_none=True'
        )


def determine_clause(value: ALLOWED_VALUES, operation: str | list[str]) -> str:
    if isinstance(value, list):
        if isinstance(operation, list):
            pairs = [
                construct_operation_value_string(v, o)
                for v, o in zip(value, operation, strict=True)
            ]
            return f'{{{" ".join(pairs)}}}'

        else:
            value = json.dumps(value)  ## is this correct for nested fields?
            return f'{{{operation}: {value}}}'
    else:
        if isinstance(operation, list):
            raise TypeError('Operation should be scalar if value is scalar')

        return f'{{{construct_operation_value_string(value, operation)}}}'


def build_clause_dict(field_name: str, clause: str) -> dict:
    fields = field_name.split('.')

    clause_dict = {fields[-1]: f'{fields[-1]}: {clause}'}
    for field in reversed(fields[:-1]):
        clause_dict = {field: clause_dict}

    return clause_dict


def build_or_and_connected_where_clause_dict_list(field_names: tuple, values: tuple, operations: tuple, skip_if_none:  tuple) -> dict:
    clause_dicts = []
    for i, field_name in enumerate(field_names):
        if isinstance(field_name, tuple):
            clause_dict_list = build_or_and_connected_where_clause_dict_list(
                field_name, values[i], operations[i], skip_if_none[i]
            )
            clause_dicts.append(clause_dict_list)
        elif not values[i]:
            if skip_if_none[i]:
                continue
            else:
                raise ValueError(
                    'Encountered None value - '
                    'if you want to skip it set skip_if_none=True'
                )
        else:
            clause = determine_clause(values[i], operations[i])
            clause_dict = build_clause_dict(field_name, clause)
            clause_dicts.append(clause_dict)
    return clause_dicts


def construct_or_and_connected_where_clauses(
    or_where_clauses: list[list[dict] | dict], binary_op: str
):
    next_binary_op = '_and' if binary_op == '_or' else '_or'
    return f"""{binary_op}: [{{{
        '} {'.join(
            [
                construct_where_clause_string(c)
                if isinstance(c, dict)
                else construct_or_and_connected_where_clauses(c, next_binary_op)
                for c in or_where_clauses
            ]
        )
    }}}]
    """
