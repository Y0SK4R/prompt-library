"""Typed records used by the persistence layer."""

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Category:
    id: int
    name: str
    created_at: str

@dataclass(frozen=True, slots=True)
class Tag:
    id: int
    name: str

@dataclass(frozen=True, slots=True)
class Prompt:
    id: int
    title: str
    description: str
    body: str
    category_id: int | None
    tags: tuple[str, ...]
    favorite: bool
    created_at: str
    updated_at: str
    deleted_at: str | None = None
