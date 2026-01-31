"""Shared Pydantic base models and helpers."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Union, get_args, get_origin
from types import UnionType

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from teachworks_sdk.models.resolvers import BaseResolver
    from teachworks_sdk.session import TeachworksSession

class TeachworksBaseModel(BaseModel):
    """Base Pydantic model for Teachworks API responses."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)
    __cacheable__: ClassVar[bool] = True

    @field_validator("*", mode="before")
    @classmethod
    def _empty_str_to_none(cls, value: Any, info) -> Any:
        if value == "":
            annotation = cls.model_fields[info.field_name].annotation
            origin = get_origin(annotation)
            if annotation in (date, datetime, time):
                return None
            if origin in (UnionType, Union):
                if any(arg in (date, datetime, time) for arg in get_args(annotation)):
                    return None
        return value

    @field_validator("*", mode="after")
    @classmethod
    def _ensure_datetime_utc(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value

    def resolve(self, session: "TeachworksSession") -> "BaseResolver[TeachworksBaseModel]":
        """Bind this model to a session for relationship lookups."""
        from teachworks_sdk.models.resolvers import get_resolver_for

        return get_resolver_for(self, session)

class LessonTotals(TeachworksBaseModel):
    """Base Pydantic model for Lesson Totals models."""
    count: int
    scheduled: int | None = Field(default=None, validation_alias="Scheduled")
    attended: int | None = Field(default=None, validation_alias="Attended")
    missed: int | None = Field(default=None, validation_alias="Missed")
    cancelled: int | None = Field(default=None, validation_alias="Cancelled")

class TeachworksErrorResponse(TeachworksBaseModel):
    """Represents an API error payload."""

    code: str | None = None
    message: str | None = None
    data: Dict[str, Any] | None = None
