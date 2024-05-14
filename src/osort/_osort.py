import ast
import re
import sys

from osort._dependencies import (
    class_statements_initialisation_graph,
    class_statements_runtime_graph,
    module_statements_graph,
)
from osort._exceptions import (
    DecodingError,
    ParseError,
    ResolutionError,
    UnknownEncodingError,
    WildcardImportError,
)
from osort._graphs import (
    is_topologically_sorted,
    replace_cycles,
    topological_sort,
)
from osort._parsing import parse, split_class
from osort._utils import (
    detect_encoding,
    detect_newline,
    normalize_newlines,
    sort_key_from_ending,
    sort_key_from_iter,
)

SPECIAL_PROPERTIES = [
    "__doc__",
    "__slots__",
]

LIFECYCLE_OPERATIONS = [
    # Lifecycle.
    "__new__",
    "__init__",
    "__del__",
    # Copying.
    "__copy__",
    "__deepcopy__",
    # Metaclasses.
    # TODO "__prepare__", ?
    "__init_subclass__",
    "__instancecheck__",
    "__subclasscheck__",
    # Generics.
    "__class_getitem__",
    # Descriptors.
    "__get__",
    "__set__",
    "__delete__",
    "__set_name__",
]

REGULAR_OPERATIONS = [
    # Callables.
    "__call__",
    # Attribute Access.
    "__getattr__",
    "__getattribute__",
    "__setattr__",
    "__delattr__",
    "__dir__",
    # Container Operations.
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__missing__",
    "__iter__",
    "__reversed__",
    "__contains__",
    "__len__",
    "__length_hint__",
    # Binary Operators.
    "__add__",
    "__radd__",
    "__iadd__",
    "__sub__",
    "__rsub__",
    "__isub__",
    "__mul__",
    "__rmul__",
    "__imul__",
    "__matmul__",
    "__rmatmul__",
    "__imatmul__",
    "__truediv__",
    "__rtruediv__",
    "__itruediv__",
    "__floordiv__",
    "__rfloordiv__",
    "__ifloordiv__",
    "__mod__",
    "__rmod__",
    "__imod__",
    "__divmod__",
    "__rdivmod__",
    "__pow__",
    "__rpow__",
    "__ipow__",
    "__lshift__",
    "__rlshift__",
    "__ilshift__",
    "__rshift__",
    "__rrshift__",
    "__irshift__",
    "__and__",
    "__rand__",
    "__iand__",
    "__xor__",
    "__rxor__",
    "__ixor__",
    "__or__",
    "__ror__",
    "__ior__",
    # Unary operators.
    "__neg__",
    "__pos__",
    "__abs__",
    "__invert__",
    # Rich comparison operators.
    "__lt__",
    "__le__",
    "__eq__",
    "__ne__",
    "__gt__",
    "__ge__",
    "__hash__",
    # Numeric conversions
    "__bool__",
    "__complex__",
    "__int__",
    "__float__",
    "__index__",
    "__round__",
    "__trunc__",
    "__floor__",
    "__ceil__",
    # Context managers.
    "__enter__",
    "__exit__",
    # Async tasks.
    "__await__",
    # Async iterators.
    "__aiter__",
    "__anext__",
    # Async context managers.
    "__aenter__",
    "__aexit__",
    # Pickling.
    "__getnewargs_ex__",
    "__reduce__",
    "__getstate__",
    "__setstate__",
    # Formatting.
    "__repr__",
    "__str__",
    "__bytes__",
    "__format__",
]

ODOO_SPECIAL_ATTRIBUTES = [
    # The attributes that come right after the fields
    "_sql_constraints",
    "init",
]

ODOO_PRIVATE_ATTRIBUTES = [
    "_name",
    "_description",
    "_inherit",
    "_inherits",
    "_abstract",
    "_active_name",
    "_allow_sudo_commands",
    "_auto",
    "_check_company_auto",
    "_custom",
    "_depends",
    "_fold_name",
    "_inherits",
    "_module",
    "_order",
    "_parent_name",
    "_parent_store",
    "_rec_name",
    "_rec_names_search",
    "_register",
    "_table",
    "_table_query",
    "_transient",
    "_translate",
    "_sql_constraints",
]

ODOO_MODEL_METHODS = [
    "__ensure_xml_id",
    "action_archive",
    "action_unarchive",
    "_add_fake_fields",
    "_add_field",
    "_add_inherited_fields",
    "_add_missing_default_values",
    "_add_precomputed_values",
    "_add_sql_constraints",
    "_apply_ir_rules",
    "_apply_onchange_methods",
    "_as_query",
    "_auto_init",
    "browse",
    "_build_model",
    "_build_model_attributes",
    "_build_model_check_base",
    "_build_model_check_parent",
    "_cache",
    "check_access_rights",
    "check_access_rule",
    "_check_company",
    "_check_company_domain",
    "check_field_access_rights",
    "_check_m2m_recursion",
    "_check_parent_path",
    "_check_qorder",
    "_check_recursion",
    "_check_removed_columns",
    "clear_caches",
    "_compute_display_name",
    "_compute_field_value",
    "_constraint_methods",
    "_convert_records",
    "_convert_to_record",
    "_convert_to_write",
    "copy",
    "copy_data",
    "copy_multi",
    "copy_translations",
    "create",
    "_create",
    "default_get",
    "_determine_fields_to_fetch",
    "ensure_one",
    "exists",
    "export_data",
    "_export_rows",
    "_extract_records",
    "fetch",
    "_fetch_field",
    "_fetch_query",
    "_field_properties_to_sql",
    "_field_to_sql",
    "fields_get",
    "_filter_access_rules",
    "_filter_access_rules_python",
    "filtered",
    "filtered_domain",
    "_flush",
    "flush_model",
    "flush_recordset",
    "_flush_search",
    "_generate_order_by",
    "_get_base_lang",
    "get_base_url",
    "get_external_id",
    "_get_external_ids",
    "get_field_translations",
    "get_metadata",
    "_get_placeholder_filename",
    "get_property_definition",
    "grouped",
    "_has_onchange",
    "ids",
    "_in_cache_without",
    "_inherits_check",
    "_inherits_join_calc",
    "init",
    "_init_column",
    "_init_constraints_onchanges",
    "_invalidate_cache",
    "invalidate_model",
    "invalidate_recordset",
    "_is_an_ordinary_table",
    "is_transient",
    "load",
    "_load_records",
    "_load_records_create",
    "_load_records_write",
    "mapped",
    "_mapped_func",
    "modified",
    "_modified",
    "_modified_triggers",
    "name_create",
    "name_get",
    "name_search",
    "_name_search",
    "new",
    "onchange",
    "_onchange_methods",
    "_ondelete_methods",
    "_order_field_to_sql",
    "_order_to_sql",
    "_origin",
    "_parent_store_compute",
    "_parent_store_create",
    "_parent_store_update",
    "_parent_store_update_prepare",
    "_pop_field",
    "_populate",
    "_populate_dependencies",
    "_populate_factories",
    "_populate_sizes",
    "_prepare_create_values",
    "_prepare_setup",
    "read",
    "_read_format",
    "read_group",
    "_read_group",
    "_read_group_check_field_access_rights",
    "_read_group_empty_value",
    "_read_group_expand_full",
    "_read_group_fill_results",
    "_read_group_fill_temporal",
    "_read_group_format_result",
    "_read_group_format_result_properties",
    "_read_group_groupby",
    "_read_group_having",
    "_read_group_orderby",
    "_read_group_postprocess_aggregate",
    "_read_group_postprocess_groupby",
    "_read_group_select",
    "_rec_name_fallback",
    "_recompute_field",
    "_recompute_model",
    "_recompute_recordset",
    "_register_hook",
    "search",
    "_search",
    "search_count",
    "search_fetch",
    "search_read",
    "_setup_base",
    "_setup_complete",
    "_setup_fields",
    "sorted",
    "sudo",
    "_table_has_rows",
    "toggle_active",
    "unlink",
    "_unregister_hook",
    "update",
    "_update_cache",
    "update_field_translations",
    "_update_field_translations",
    "user_has_groups",
    "_valid_field_parameter",
    "_validate_fields",
    "_where_calc",
    "with_company",
    "with_context",
    "with_env",
    "with_prefetch",
    "with_user",
    "write",
    "_write",
]


def _partition(values, predicate):
    passed = []
    failed = []

    for value in values:
        if predicate(value):
            passed.append(value)
        else:
            failed.append(value)
    return passed, failed


def _is_string(statement):
    expr_node = statement.node
    if not isinstance(expr_node, ast.Expr):
        return False

    node = expr_node.value
    if not isinstance(node, ast.Constant):
        return False

    return isinstance(node.value, str)


def _is_special_property(statement):
    return any(
        binding in SPECIAL_PROPERTIES for binding in statement.bindings()
    )


def _is_odoo_special_attribute(statement):
    return any(
        binding in ODOO_SPECIAL_ATTRIBUTES for binding in statement.bindings()
    )


def _is_lifecycle_operation(statement):
    return any(
        binding in LIFECYCLE_OPERATIONS for binding in statement.bindings()
    )


def _is_regular_operation(statement):
    return any(
        binding in REGULAR_OPERATIONS for binding in statement.bindings()
    )


def _is_odoo_private_attribute(statement):
    return isinstance(
        statement.node, (ast.Assign, ast.AnnAssign, ast.AugAssign)
    ) and any(
        binding in ODOO_PRIVATE_ATTRIBUTES for binding in statement.bindings()
    )


def _is_private_attribute(statement):
    return isinstance(
        statement.node, (ast.Assign, ast.AnnAssign, ast.AugAssign)
    ) and all(
        binding.startswith("_")  # all part is not required I guess
        and binding not in ODOO_PRIVATE_ATTRIBUTES
        for binding in statement.bindings()
    )


def _is_field(statement):
    return (
        isinstance(statement.node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        and all(
            not binding.startswith("_") for binding in statement.bindings()
        )
        and statement.text.find("fields.") > 0
    )


def _is_property(statement):
    return isinstance(
        statement.node, (ast.Assign, ast.AnnAssign, ast.AugAssign)
    )


def _is_default_method(statement):
    return isinstance(statement.node, ast.FunctionDef) and all(
        binding == "default_get" or binding.startswith("_default_")
        for binding in statement.bindings()
    )


def _is_compute_method(statement):
    return isinstance(statement.node, ast.FunctionDef) and (
        any(
            isinstance(dec, ast.Call) and dec.func.attr == "depends"
            for dec in statement.node.decorator_list
        )
        or all(
            binding.startswith("_compute_")
            or binding.startswith("_inverse_")
            or binding.startswith("_search_")
            for binding in statement.bindings()
        )
    )


def _is_selection_method(statement):
    return isinstance(statement.node, ast.FunctionDef) and all(
        binding.startswith("_selection_") for binding in statement.bindings()
    )


def _is_constraint_method(statement):
    return isinstance(statement.node, ast.FunctionDef) and any(
        isinstance(dec, ast.Call) and dec.func.attr == "constrains"
        for dec in statement.node.decorator_list
    )


def _is_onchange_method(statement):
    return isinstance(statement.node, ast.FunctionDef) and any(
        isinstance(dec, ast.Call) and dec.func.attr == "onchange"
        for dec in statement.node.decorator_list
    )


def _is_orm_override(statement):
    return isinstance(statement.node, ast.FunctionDef) and any(
        binding in ODOO_MODEL_METHODS for binding in statement.bindings()
    )


def _is_action(statement):
    return isinstance(statement.node, ast.FunctionDef) and any(
        binding.startswith("action_") for binding in statement.bindings()
    )


def _is_class(statement):
    return isinstance(statement.node, ast.ClassDef)


def _statement_binding_sort_key(binding_key):
    def _safe_binding_key(binding):
        try:
            return binding_key(binding)
        except KeyError:
            return sys.maxsize

    def _key(statement):
        """
        Returns a tuple of (key, binding) to sort the statements on the binding_key first,
        and then alphabetically on their binding. Alphabetic sorting will work for the cases when
        no key is found for the binding as well as when there are several similar methods and sort
        key is based on the ending, e.g. _compute_field, _search_field, _inverse_field, etc.
        """
        bindings = statement.bindings()
        return (
            min(_safe_binding_key(binding) for binding in bindings),
            bindings[0],
        )

    return _key


def _statement_text_sorted_class(statement, sort_fields=False):
    head_text, unsorted_statements = split_class(statement)

    statements = list(unsorted_statements)

    # Take a snapshot of any hard dependencies between statements so that we can
    # restore them later.
    initialisation_graph = class_statements_initialisation_graph(statements)

    # === Split up the statements into high level groups =======================
    if _is_string(statements[0]):
        docstrings, statements = statements[:1], statements[1:]
    else:
        docstrings = []

    # General class stuff
    special_properties, statements = _partition(
        statements, _is_special_property
    )

    lifecycle_operations, statements = _partition(
        statements, _is_lifecycle_operation
    )

    regular_operations, statements = _partition(
        statements, _is_regular_operation
    )

    inner_classes, statements = _partition(statements, _is_class)

    # add a special case for init (and perhaps _sql_constrain because despite the guideline, it always comes after
    # fields)
    odoo_special_attributes, statements = _partition(
        statements, _is_odoo_special_attribute
    )

    odoo_private_attributes, statements = _partition(
        statements, _is_odoo_private_attribute
    )

    other_private_attributes, statements = _partition(
        statements, _is_private_attribute
    )

    orm_overrides, statements = _partition(statements, _is_orm_override)

    default_methods, statements = _partition(statements, _is_default_method)

    odoo_fields, statements = _partition(statements, _is_field)

    compute_methods, statements = _partition(statements, _is_compute_method)

    selection_methods, statements = _partition(
        statements, _is_selection_method
    )

    constraint_methods, statements = _partition(
        statements, _is_constraint_method
    )

    onchange_methods, statements = _partition(statements, _is_onchange_method)

    actions, statements = _partition(statements, _is_action)

    properties, statements = _partition(statements, _is_property)

    methods, statements = statements, []

    fields = [statement.bindings()[0] for statement in odoo_fields]
    if sort_fields:
        fields = sorted(fields)

    sorted_statements = []

    # === Join groups back together in the correct order =======================
    sorted_statements += docstrings

    # Special properties (in hard-coded order).
    sorted_statements += sorted(
        special_properties,
        key=_statement_binding_sort_key(
            sort_key_from_iter(SPECIAL_PROPERTIES)
        ),
    )

    # Inner classes (in original order).
    sorted_statements += inner_classes

    # Odoo private attributes (in hard-coded order).
    sorted_statements += sorted(
        odoo_private_attributes,
        key=_statement_binding_sort_key(
            sort_key_from_iter(ODOO_PRIVATE_ATTRIBUTES)
        ),
    )

    # Other private attributes (in origial order).
    sorted_statements += other_private_attributes

    # Default methods (in fields order, put default_get first).
    sorted_statements += sorted(
        default_methods,
        key=lambda binding: (
            -1
            if binding == "default_get"
            else _statement_binding_sort_key(
                sort_key_from_ending(default_methods, fields)
            )
        ),
    )

    # Regular properties (in original order).
    sorted_statements += properties

    # Odoo fields (in original order or sorted).
    sorted_statements += (
        sorted(odoo_fields, key=lambda field: field.bindings()[0])
        if sort_fields
        else odoo_fields
    )

    # Odoo special attributes (in hard-coded order).
    # These are the ones that come right after fields definition

    sorted_statements += sorted(
        odoo_special_attributes,
        key=_statement_binding_sort_key(
            sort_key_from_iter(ODOO_SPECIAL_ATTRIBUTES)
        ),
    )

    # Special class lifecycle methods (in hard-coded order).
    sorted_statements += sorted(
        lifecycle_operations,
        key=_statement_binding_sort_key(
            sort_key_from_iter(LIFECYCLE_OPERATIONS)
        ),
    )

    # Compute methods (in fields order).
    sorted_statements += sorted(
        compute_methods,
        key=_statement_binding_sort_key(
            sort_key_from_ending(compute_methods, fields)
        ),
    )

    # Selection methods (in fields order).

    sorted_statements += sorted(
        selection_methods,
        key=_statement_binding_sort_key(
            sort_key_from_ending(selection_methods, fields)
        ),
    )

    # Constraint methods (in fields order).
    sorted_statements += sorted(
        constraint_methods,
        key=_statement_binding_sort_key(
            sort_key_from_ending(constraint_methods, fields)
        ),
    )

    # Onchange methods (in fields order).
    sorted_statements += sorted(
        onchange_methods,
        key=_statement_binding_sort_key(
            sort_key_from_ending(onchange_methods, fields)
        ),
    )

    # ORM overrides (in hard-coded order).
    sorted_statements += sorted(
        orm_overrides,
        key=_statement_binding_sort_key(
            sort_key_from_iter(ODOO_MODEL_METHODS)
        ),
    )

    # Action methods (in original order).
    sorted_statements += actions

    # Regular methods.
    sorted_statements += methods

    # Special operations (in hard-coded order).
    sorted_statements += sorted(
        regular_operations,
        key=_statement_binding_sort_key(
            sort_key_from_iter(REGULAR_OPERATIONS)
        ),
    )

    # === Re-sort based on dependencies between statements =====================

    # Fix any hard dependencies.
    sorted_statements = topological_sort(
        sorted_statements, graph=initialisation_graph
    )

    # Attempt to resolve soft dependencies on private attributes, but with hard
    # dependencies taking priority, and always preserving the original order
    # where there are cycles.
    runtime_graph = class_statements_runtime_graph(
        sorted_statements, ignore_public=True
    )
    runtime_graph.update(initialisation_graph)
    replace_cycles(runtime_graph, key=sort_key_from_iter(sorted_statements))

    sorted_statements = topological_sort(
        sorted_statements, graph=runtime_graph
    )

    if sorted_statements == unsorted_statements:
        return statement.text

    return (
        head_text
        + "\n"
        + "\n".join(
            statement_text_sorted(body_statement, sort_fields=sort_fields)
            for body_statement in sorted_statements
        )
    )


def statement_text_sorted(statement, sort_fields=False):
    node = statement.node
    if isinstance(node, ast.ClassDef):
        return _statement_text_sorted_class(statement, sort_fields=sort_fields)
    return statement.text


def _on_unknown_encoding_ignore(message, **kwargs):
    pass


def _on_unknown_encoding_raise(message, *, encoding, **kwargs):
    raise UnknownEncodingError(message, encoding=encoding)


def _interpret_on_unknown_encoding_action(on_unknown_encoding):
    if on_unknown_encoding == "ignore":
        return _on_unknown_encoding_ignore

    if on_unknown_encoding == "raise":
        return _on_unknown_encoding_raise

    return on_unknown_encoding


def _on_decoding_error_ignore(message, **kwargs):
    pass


def _on_decoding_error_raise(message, **kwargs):
    raise DecodingError(message)


def _interpret_on_decoding_error_action(on_decoding_error):
    if on_decoding_error == "ignore":
        return _on_decoding_error_ignore

    if on_decoding_error == "raise":
        return _on_decoding_error_raise

    return on_decoding_error


def _on_parse_error_ignore(message, **kwargs):
    pass


def _on_parse_error_raise(message, *, lineno, col_offset, **kwargs):
    raise ParseError(message, lineno=lineno, col_offset=col_offset)


def _interpret_on_parse_error_action(on_parse_error):
    if on_parse_error == "ignore":
        return _on_parse_error_ignore

    if on_parse_error == "raise":
        return _on_parse_error_raise

    return on_parse_error


def _on_unresolved_ignore(message, *, name, lineno, col_offset, **kwargs):
    pass


def _on_unresolved_raise(message, *, name, lineno, col_offset, **kwargs):
    raise ResolutionError(
        message,
        name=name,
        lineno=lineno,
        col_offset=col_offset,
    )


def _interpret_on_unresolved_action(on_unresolved):
    if on_unresolved == "ignore":
        return _on_unresolved_ignore

    if on_unresolved == "raise":
        return _on_unresolved_raise

    return on_unresolved


def _on_wildcard_import_ignore(**kwargs):
    pass


def _on_wildcard_import_raise(*, lineno, col_offset, **kwargs):
    raise WildcardImportError(
        "can't reliably determine dependencies on * import",
        lineno=lineno,
        col_offset=col_offset,
    )


def _interpret_on_wildcard_import_action(on_wildcard_import):
    if on_wildcard_import == "ignore":
        return _on_wildcard_import_ignore

    if on_wildcard_import == "raise":
        return _on_wildcard_import_raise

    return on_wildcard_import


def osort(
    text,
    *,
    filename="<unknown>",
    sort_fields=False,
    on_unknown_encoding_error="raise",
    on_decoding_error="raise",
    on_parse_error="raise",
    on_unresolved="raise",
    on_wildcard_import="raise",
):
    on_unknown_encoding_error = _interpret_on_unknown_encoding_action(
        on_unknown_encoding_error
    )
    on_decoding_error = _interpret_on_decoding_error_action(on_decoding_error)
    on_parse_error = _interpret_on_parse_error_action(on_parse_error)
    on_unresolved = _interpret_on_unresolved_action(on_unresolved)
    on_wildcard_import = _interpret_on_wildcard_import_action(
        on_wildcard_import
    )

    try:
        encoding = None
        if isinstance(text, bytes):
            encoding = detect_encoding(text)
            text = text.decode(encoding)
    except UnknownEncodingError as exc:
        on_unknown_encoding_error(str(exc), encoding=exc.encoding)
        return text

    except UnicodeDecodeError as exc:
        on_decoding_error(str(exc))
        return text

    newline = detect_newline(text)
    text = normalize_newlines(text)

    try:
        statements = list(parse(text, filename=filename))
    except ParseError as exc:
        on_parse_error(str(exc), lineno=exc.lineno, col_offset=exc.col_offset)
        return text

    if not statements:
        return text

    graph = module_statements_graph(
        statements,
        on_unresolved=on_unresolved,
        on_wildcard_import=on_wildcard_import,
    )
    if graph is None:
        return text

    replace_cycles(graph, key=sort_key_from_iter(statements))

    sorted_statements = topological_sort(statements, graph=graph)

    assert is_topologically_sorted(sorted_statements, graph=graph)

    output = "\n".join(
        statement_text_sorted(statement, sort_fields=sort_fields)
        for statement in sorted_statements
    )
    if output:
        output += "\n"

    if newline != "\n":
        output = re.sub("\n", newline, output)
    if encoding is not None:
        output = output.encode(encoding)
    return output
