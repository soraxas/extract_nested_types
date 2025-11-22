import types
from dataclasses import fields, is_dataclass
from typing import Annotated, Any, List, Tuple, Union, get_args, get_origin

from pydantic import BaseModel

DEFAULT_IGNORE: set[Any] = {
    type(None),
    type(Ellipsis),
    # union types
    types.UnionType,
    Union,
    list,
    List,
    Annotated,
    tuple,
    Tuple,
}


def extract_all_nested_types(
    root_type: Any, *, ignore: set[type] | None = DEFAULT_IGNORE
) -> set[type]:
    """
    Extract all nested types from an annotation.
    """
    out = extract_all_nested_types_recursive(root_type, seen=set())
    if ignore is not None:
        out -= ignore
    return out


def extract_all_nested_types_recursive(
    root_type: Any,
    seen: set[Any] | None = None,
) -> set[type]:
    """
    Recursively extract ALL nested Python types from any annotation.
    Returns a set containing:
        - builtin types (str, int, ...)
        - collection origins (list, dict, set...)
        - Pydantic models (BaseModel subclasses)
        - dataclasses
        - nested types inside generics / unions / annotated

    Examples:
        Optional[List[User]] → {list, User}
        dict[str, list[Address]] → {dict, str, list, Address}
        User(BaseModel) → includes nested model fields
        Config(dataclass) → includes nested field types
    """
    if seen is None:
        seen = set()

    # Prevent recursion cycles
    if root_type in seen:
        return set()
    seen.add(root_type)

    result: set[type] = set()

    origin = get_origin(root_type)
    args = get_args(root_type)

    # ------------------------------------------------------------
    # 1. Pydantic BaseModel (class)
    # ------------------------------------------------------------
    if isinstance(root_type, type) and issubclass(root_type, BaseModel):
        result.add(root_type)

        for field in root_type.model_fields.values():
            result |= extract_all_nested_types_recursive(field.annotation, seen)

        return result

    # ------------------------------------------------------------
    # 2. Dataclass (class)
    # ------------------------------------------------------------
    if isinstance(root_type, type) and is_dataclass(root_type):
        result.add(root_type)

        for f in fields(root_type):
            if f.type:
                result |= extract_all_nested_types_recursive(f.type, seen)

        return result

    # ------------------------------------------------------------
    # 3. Non-generic built-in or normal class type
    # ------------------------------------------------------------
    if origin is None:
        # None / type(None) → ignore
        if root_type is None or root_type is type(None):
            return result

        # Real class?
        if isinstance(root_type, type):
            result.add(root_type)

        return result

    # ------------------------------------------------------------
    # 4. Generic types (List[T], Dict[K,V], tuple[X], set[Y], etc.)
    # ------------------------------------------------------------
    result.add(origin)

    # Optional, Union, Annotated, PEP 604
    if origin is Union:
        for arg in args:
            if arg is not type(None):  # Optional[T]
                result |= extract_all_nested_types_recursive(arg, seen)
        return result

    if origin is Annotated:
        # Annotated[T, ...] → T only
        real_type = args[0]
        result |= extract_all_nested_types_recursive(real_type, seen)
        return result

    # Normal generics
    for arg in args:
        result |= extract_all_nested_types_recursive(arg, seen)

    return result
