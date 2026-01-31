from enum import IntEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from markdantic import generator

expected = """
## `B`

**Base:** `BaseModel`

B class

**Parameters:**

|Name|Type|Description|Default|
|---|---|---|---|
|`v001`|`int`|`v001` is cool.|_Required_|
|`v002`|`float`||_Required_|
|`v003`|`str`||_Required_|
|`v004`|`test_generator.A`||_Required_|
|`v005`|`pathlib.Path`||_Required_|
|`v006`|`test_generator.E`|`v006` is cool. (members: 1=`NO`, 2=`YES`)|_Required_|
|`v007`|`Any`||_Required_|
|`v008`|`str`||`''`|
|`v009`|`str`||`''`|
|`v011`|`int｜None`|value can be int ｜ None|`None`|
|`v012`|`float｜None`||`None`|
|`v013`|`str｜None`||`None`|
|`v014`|`test_generator.A｜None`||`None`|
|`v015`|`pathlib.Path｜None`||`None`|
|`v016`|`test_generator.E｜None`||`None`|
|`v017`|`Any｜None`||`None`|
|`v021`|`list`||_Required_|
|`v022`|`list`||`[]`|
|`v031`|`dict`||_Required_|
|`v032`|`dict`||`{}`|
|`v041`|`set`||_Required_|
|`v042`|`set`||`set()`|
|`v051`|`tuple`||_Required_|
|`v052`|`tuple`||`tuple()`|
|`v211`|`list[int]`||_Required_|
|`v212`|`list[float]`||_Required_|
|`v213`|`list[str]`||_Required_|
|`v214`|`list[test_generator.A]`||_Required_|
|`v215`|`list[pathlib.Path]`||_Required_|
|`v216`|`list[test_generator.E]`||_Required_|
|`v217`|`list[Any]`||_Required_|
|`v221`|`list[int]｜None`||`None`|
|`v222`|`list[float]｜None`||`None`|
|`v223`|`list[str]｜None`||`None`|
|`v224`|`list[test_generator.A]｜None`||`None`|
|`v225`|`list[pathlib.Path]｜None`||`None`|
|`v226`|`list[test_generator.E]｜None`||`None`|
|`v227`|`list[Any]｜None`||`None`|
|`v311`|`dict[str, int]`||_Required_|
|`v312`|`dict[str, float]`||_Required_|
|`v313`|`dict[str, str]`||_Required_|
|`v314`|`dict[str, test_generator.A]`||_Required_|
|`v315`|`dict[str, pathlib.Path]`||_Required_|
|`v316`|`dict[str, test_generator.E]`||_Required_|
|`v317`|`dict[str, Any]`||_Required_|
|`v321`|`dict[str, list[int]]`||_Required_|
|`v322`|`dict[str, list[float]]`||_Required_|
|`v323`|`dict[str, list[str]]`||_Required_|
|`v324`|`dict[str, list[test_generator.A]]`||_Required_|
|`v325`|`dict[str, list[pathlib.Path]]`||_Required_|
|`v326`|`dict[str, list[test_generator.E]]`||_Required_|
|`v327`|`dict[str, list[Any]]`||_Required_|
|`v411`|`set[int]`||_Required_|
|`v412`|`set[float]`||_Required_|
|`v413`|`set[str]`||_Required_|
|`v414`|`set[test_generator.A]`||_Required_|
|`v415`|`set[pathlib.Path]`||_Required_|
|`v416`|`set[test_generator.E]`||_Required_|
|`v417`|`set[Any]`||_Required_|
|`v512`|`tuple[float]`||_Required_|
|`v513`|`tuple[str]`||_Required_|
|`v514`|`tuple[test_generator.A]`||_Required_|
|`v515`|`tuple[pathlib.Path]`||_Required_|
|`v516`|`tuple[test_generator.E]`||_Required_|
|`v517`|`tuple[Any]`||_Required_|
|`v521`|`tuple[int, ...]`||_Required_|
|`v522`|`tuple[float, ...]`||_Required_|
|`v523`|`tuple[str, ...]`||_Required_|
|`v524`|`tuple[test_generator.A, ...]`||_Required_|
|`v525`|`tuple[pathlib.Path, ...]`||_Required_|
|`v526`|`tuple[test_generator.E, ...]`||_Required_|
|`v527`|`tuple[Any, ...]`||_Required_|"""


BASE = Path(__file__).parent


class E(IntEnum):
    NO = 1
    YES = 2


class A(BaseModel):
    a: int


class B(BaseModel):
    """B class"""

    v001: int = Field(..., description="`v001` is cool.")
    v002: float = Field(...)
    v003: str = Field(...)
    v004: A = Field(...)
    v005: Path = Field(...)
    v006: E = Field(..., description="`v006` is cool.")
    v007: Any = Field(...)
    v008: str = Field("")
    # fmt: off
    v009: str = Field('')
    # fmt: on

    v011: int | None = Field(None, description="value can be int | None")
    v012: float | None = Field(None)
    v013: str | None = Field(None)
    v014: A | None = Field(None)
    v015: Path | None = Field(None)
    v016: E | None = Field(None)
    v017: Any | None = Field(None)

    v021: list = Field(...)
    v022: list = Field(default_factory=list)

    v031: dict = Field(...)
    v032: dict = Field(default_factory=dict)

    v041: set = Field(...)
    v042: set = Field(default_factory=set)

    v051: tuple = Field(...)
    v052: tuple = Field(default_factory=tuple)

    v211: list[int] = Field(...)
    v212: list[float] = Field(...)
    v213: list[str] = Field(...)
    v214: list[A] = Field(...)
    v215: list[Path] = Field(...)
    v216: list[E] = Field(...)
    v217: list[Any] = Field(...)

    v221: list[int] | None = Field(None)
    v222: list[float] | None = Field(None)
    v223: list[str] | None = Field(None)
    v224: list[A] | None = Field(None)
    v225: list[Path] | None = Field(None)
    v226: list[E] | None = Field(None)
    v227: list[Any] | None = Field(None)

    v311: dict[str, int] = Field(...)
    v312: dict[str, float] = Field(...)
    v313: dict[str, str] = Field(...)
    v314: dict[str, A] = Field(...)
    v315: dict[str, Path] = Field(...)
    v316: dict[str, E] = Field(...)
    v317: dict[str, Any] = Field(...)

    v321: dict[str, list[int]] = Field(...)
    v322: dict[str, list[float]] = Field(...)
    v323: dict[str, list[str]] = Field(...)
    v324: dict[str, list[A]] = Field(...)
    v325: dict[str, list[Path]] = Field(...)
    v326: dict[str, list[E]] = Field(...)
    v327: dict[str, list[Any]] = Field(...)

    v411: set[int] = Field(...)
    v412: set[float] = Field(...)
    v413: set[str] = Field(...)
    v414: set[A] = Field(...)
    v415: set[Path] = Field(...)
    v416: set[E] = Field(...)
    v417: set[Any] = Field(...)

    v512: tuple[float] = Field(...)
    v513: tuple[str] = Field(...)
    v514: tuple[A] = Field(...)
    v515: tuple[Path] = Field(...)
    v516: tuple[E] = Field(...)
    v517: tuple[Any] = Field(...)

    v521: tuple[int, ...] = Field(...)
    v522: tuple[float, ...] = Field(...)
    v523: tuple[str, ...] = Field(...)
    v524: tuple[A, ...] = Field(...)
    v525: tuple[Path, ...] = Field(...)
    v526: tuple[E, ...] = Field(...)
    v527: tuple[Any, ...] = Field(...)


def test_generator():
    assert generator(B) == expected
