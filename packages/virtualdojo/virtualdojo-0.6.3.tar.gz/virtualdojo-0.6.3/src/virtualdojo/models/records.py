"""Record-related models."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Record(BaseModel):
    """Generic record model."""

    id: str
    tenant_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    is_deleted: bool = False

    class Config:
        extra = "allow"  # Allow extra fields


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""

    data: list[T]
    total: int
    skip: int = 0
    limit: int = 100


class ObjectDefinition(BaseModel):
    """Object/table definition."""

    api_name: str
    label: str
    plural_label: str | None = None
    description: str | None = None
    is_custom: bool = False
    field_count: int | None = None


class FieldDefinition(BaseModel):
    """Field definition."""

    api_name: str
    label: str
    field_type: str
    is_required: bool = False
    is_unique: bool = False
    max_length: int | None = None
    default_value: Any | None = None
    help_text: str | None = None
    picklist_values: list[dict[str, Any]] | None = None


class ObjectSchema(BaseModel):
    """Complete object schema with fields."""

    object: ObjectDefinition
    fields: list[FieldDefinition]
