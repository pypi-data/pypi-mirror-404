"""
Pydantic compatibility layer for v1 and v2.
"""

from typing import TypeVar, Type

try:
    from pydantic import VERSION as PYDANTIC_VERSION
    PYDANTIC_V2 = PYDANTIC_VERSION.startswith("2.")
except ImportError:
    PYDANTIC_V2 = False

T = TypeVar("T")


def model_validate(cls: Type[T], data: dict) -> T:
    """Validate data and create model instance.
    
    Works with both Pydantic v1 and v2.
    """
    if PYDANTIC_V2:
        return cls.model_validate(data)  # type: ignore
    else:
        return cls.parse_obj(data)  # type: ignore


def model_dump(instance, exclude_none: bool = False) -> dict:
    """Dump model to dict.
    
    Works with both Pydantic v1 and v2.
    """
    if PYDANTIC_V2:
        return instance.model_dump(exclude_none=exclude_none)
    else:
        return instance.dict(exclude_none=exclude_none)
