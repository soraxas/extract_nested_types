from dataclasses import dataclass
from types import UnionType
from typing import Annotated, Dict, List, Optional, Union

from pydantic import BaseModel

from type_extractor import extract_all_nested_types

# ------------------------------------------------------------
# Pydantic Models
# ------------------------------------------------------------


class Address(BaseModel):
    street: str
    zip: int
    latitude: float


class User(BaseModel):
    id: int
    address: Address
    tags: Optional[List[str]]  # Optional[List[str]]


def test_pydantic_nested_types():
    types = extract_all_nested_types(User)

    assert types == {
        User,
        Address,
        int,
        str,
        float,
    }


# ------------------------------------------------------------
# Dataclasses
# ------------------------------------------------------------


@dataclass
class Config:
    retries: int
    servers: Dict[str, List[int]]


def test_dataclass_nested_types():
    types = extract_all_nested_types(Config)

    assert types == {
        Config,
        int,
        dict,
        str,
    }


# ------------------------------------------------------------
# PEP 604 union support (A | B)
# ------------------------------------------------------------


def test_pep604_union():
    typ = int | str
    types = extract_all_nested_types(typ)

    assert types == {int, str}


# ------------------------------------------------------------
# Union + Optional
# ------------------------------------------------------------


def test_optional_union():
    typ = Optional[User]  # Union[User, None]
    types = extract_all_nested_types(typ, ignore=None)

    assert types == {
        User,
        Address,
        int,
        str,
        float,
        list,
        Union,
    }


# ------------------------------------------------------------
# Annotated
# ------------------------------------------------------------


def test_annotated():
    typ = Annotated[List[int], "meta"]
    types = extract_all_nested_types(typ, ignore=None)

    assert types == {
        list,
        int,
        Annotated,
    }


# ------------------------------------------------------------
# Deep nested generics
# ------------------------------------------------------------


def test_deep_nested_generics():
    typ = Dict[str, List[Dict[int, List[User]]]]

    types = extract_all_nested_types(typ)

    assert types == {
        float,
        dict,
        str,
        int,
        User,
        Address,
    }


# ------------------------------------------------------------
# Mixed dataclass + pydantic
# ------------------------------------------------------------


@dataclass
class Job:
    config: Config
    assigned_to: User | None


def test_mixed_pydantic_and_dataclass():
    types = extract_all_nested_types(Job, ignore=None)

    assert types == {
        Job,
        Union,
        float,
        UnionType,
        Config,
        User,
        Address,
        dict,
        list,
        int,
        str,
    }


# ------------------------------------------------------------
# Recursive types / cycle detection
# ------------------------------------------------------------


@dataclass
class Node:
    value: int
    next: "Node | None"


def test_cycle_detection():
    types = extract_all_nested_types(Node)

    # The function must NOT infinite loop
    assert types == {
        Node,
        int,
    }


# ------------------------------------------------------------
# Basic builtin types
# ------------------------------------------------------------


def test_builtin():
    assert extract_all_nested_types(int) == {int}
    assert extract_all_nested_types(str) == {str}
    assert extract_all_nested_types(dict) == {dict}
