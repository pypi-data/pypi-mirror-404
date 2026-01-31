"""Typed list query parameter models for Teachworks list endpoints."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date as Date, datetime as DateTime, time as Time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _serialize_value(value: Any) -> Any:
    if isinstance(value, DateTime):
        return value.isoformat()
    if isinstance(value, Date):
        return value.isoformat()
    if isinstance(value, Time):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


class ListParamsBase(BaseModel):
    """Base class for list query parameter models."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _reject_pagination_fields(cls, data: Any) -> Any:
        if isinstance(data, Mapping):
            disallowed = {"page", "per_page"} & set(data)
            if disallowed:
                raise ValueError(
                    "Pagination fields are not supported on list query params. "
                    "Use client.list(page=..., per_page=...) instead."
                )
        return data

    def to_query_params(self) -> dict[str, Any]:
        """Serialize the model to API query parameters."""
        data = self.model_dump(mode='json', exclude_none=True, by_alias=True)
        if not data:
            return {}
        return {key: _serialize_value(value) for key, value in data.items()}


class AvailabilityListParams(ListParamsBase):
    employee_id: int | None = Field(default=None, description="search by employee id")
    day: int | None = Field(default=None, description="search by day of week (Sunday = 0)")
    start_time: Time | None = Field(
        default=None,
        serialization_alias="start_time",
        description="search by start time (HH:MM:SS)",
    )
    end_time: Time | None = Field(
        default=None,
        serialization_alias="end_time",
        description="search by end time (HH:MM:SS)",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class CostPremiumListParams(ListParamsBase):
    name: str | None = Field(default=None, description="search by name")
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class CreditNoteAllocationListParams(ListParamsBase):
    credit_note_id: int | None = Field(default=None, description="search by credit note id")
    invoice_id: int | None = Field(default=None, description="search by invoice id")
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class CustomerListParams(ListParamsBase):
    first_name: str | None = Field(default=None, description="search by first name")
    last_name: str | None = Field(default=None, description="search by last name")
    email: str | None = Field(default=None, description="search by email")
    phone_number: str | None = Field(default=None, description="search by phone number")
    city: str | None = Field(default=None, description="search by city")
    state: str | None = Field(default=None, description="search by state")
    zip: str | None = Field(default=None, description="search by zip")
    country: str | None = Field(default=None, description="search by country")
    customer_type: str | None = Field(
        default=None,
        serialization_alias="type",
        description="search by customer type (family or independent)",
    )
    status: str | None = Field(
        default=None,
        description="search by status (Active, Inactive, Prospective)",
    )
    id_gt: int | None = Field(
        default=None,
        serialization_alias="id[gt]",
        description="search where id is greater than",
    )
    id_lt: int | None = Field(
        default=None,
        serialization_alias="id[lt]",
        description="search where id is less than",
    )
    id_gte: int | None = Field(
        default=None,
        serialization_alias="id[gte]",
        description="search where id is equal to or greater than",
    )
    id_lte: int | None = Field(
        default=None,
        serialization_alias="id[lte]",
        description="search where id is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class EmployeeListParams(ListParamsBase):
    first_name: str | None = Field(default=None, description="search by first name")
    last_name: str | None = Field(default=None, description="search by last name")
    email: str | None = Field(default=None, description="search by email")
    city: str | None = Field(default=None, description="search by city")
    state: str | None = Field(default=None, description="search by state")
    zip: str | None = Field(default=None, description="search by zip")
    status: str | None = Field(
        default=None,
        description="search by status (Active, Inactive, Prospective)",
    )
    subject: str | None = Field(default=None, description="search by subject")
    id_gt: int | None = Field(
        default=None,
        serialization_alias="id[gt]",
        description="search where id is greater than",
    )
    id_lt: int | None = Field(
        default=None,
        serialization_alias="id[lt]",
        description="search where id is less than",
    )
    id_gte: int | None = Field(
        default=None,
        serialization_alias="id[gte]",
        description="search where id is equal to or greater than",
    )
    id_lte: int | None = Field(
        default=None,
        serialization_alias="id[lte]",
        description="search where id is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class InvoiceListParams(ListParamsBase):
    customer_id: int | None = Field(default=None, description="search by customer id")
    number: int | None = Field(default=None, description="search by invoice number")
    status: str | None = Field(default=None, description="search by status (Saved, Approved, Paid, Void)")
    date: Date | None = Field(default=None, description="search by invoice date. Use YYYY-MM-DD format.")
    date_gt: Date | None = Field(
        default=None,
        serialization_alias="date[gt]",
        description="search where date is greater than",
    )
    date_lt: Date | None = Field(
        default=None,
        serialization_alias="date[lt]",
        description="search where date is less than",
    )
    date_gte: Date | None = Field(
        default=None,
        serialization_alias="date[gte]",
        description="search where date is equal to or greater than",
    )
    date_lte: Date | None = Field(
        default=None,
        serialization_alias="date[lte]",
        description="search where date is equal to or less than",
    )
    due_date: Date | None = Field(default=None, description="search by due date")
    due_date_gt: Date | None = Field(
        default=None,
        serialization_alias="due_date[gt]",
        description="search where date is greater than",
    )
    due_date_lt: Date | None = Field(
        default=None,
        serialization_alias="due_date[lt]",
        description="search where date is less than",
    )
    due_date_gte: Date | None = Field(
        default=None,
        serialization_alias="due_date[gte]",
        description="search where date is equal to or greater than",
    )
    due_date_lte: Date | None = Field(
        default=None,
        serialization_alias="due_date[lte]",
        description="search where date is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class LessonListParams(ListParamsBase):
    name: str | None = Field(default=None, description="search by name")
    series_id: int | None = Field(
        default=None,
        description="search by series id for repeating lessons",
    )
    location_id: int | None = Field(default=None, description="search by location id")
    location_or_parent_location_id: int | None = Field(
        default=None,
        description=(
            "search by location or parent location id (ie. if lesson location is a sub-location, "
            "this will match on the sub-location or parent location)"
        ),
    )
    employee_id: int | None = Field(default=None, description="search by teacher id")
    service_id: int | None = Field(default=None, description="search by service id")
    student_id: int | None = Field(default=None, description="search by student id")
    status: str | None = Field(default=None, description="search by status")
    custom_status: str | None = Field(default=None, description="search by custom status")
    from_date: Date | None = Field(
        default=None,
        description="search by date the lesson starts on. Use YYYY-MM-DD format.",
    )
    from_date_gt: Date | None = Field(
        default=None,
        serialization_alias="from_date[gt]",
        description="search where start date is greater than",
    )
    from_date_lt: Date | None = Field(
        default=None,
        serialization_alias="from_date[lt]",
        description="search where start date is less than",
    )
    from_date_gte: Date | None = Field(
        default=None,
        serialization_alias="from_date[gte]",
        description="search where start date is equal to or greater than",
    )
    from_date_lte: Date | None = Field(
        default=None,
        serialization_alias="from_date[lte]",
        description="search where start date is equal to or less than",
    )
    to_date: Date | None = Field(
        default=None,
        description="search by date the lesson ends on. Use YYYY-MM-DD format.",
    )
    to_date_gt: Date | None = Field(
        default=None,
        serialization_alias="to_date[gt]",
        description="search where lesson end date is greater than",
    )
    to_date_lt: Date | None = Field(
        default=None,
        serialization_alias="to_date[lt]",
        description="search where lesson end date is less than",
    )
    to_date_gte: Date | None = Field(
        default=None,
        serialization_alias="to_date[gte]",
        description="search where lesson end date is equal to or greater than",
    )
    to_date_lte: Date | None = Field(
        default=None,
        serialization_alias="to_date[lte]",
        description="search where lesson end date is equal to or less than",
    )
    id: int | None = Field(default=None, description="search lesson id")
    id_gt: int | None = Field(
        default=None,
        serialization_alias="id[gt]",
        description="search where id is greater than",
    )
    id_lt: int | None = Field(
        default=None,
        serialization_alias="id[lt]",
        description="search where id is less than",
    )
    id_gte: int | None = Field(
        default=None,
        serialization_alias="id[gte]",
        description="search where id is equal to or greater than",
    )
    id_lte: int | None = Field(
        default=None,
        serialization_alias="id[lte]",
        description="search where id is equal to or less than",
    )
    joinable: bool | None = Field(
        default=None,
        description="set to true to only list lessons marked as joinable",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class LessonParticipantListParams(ListParamsBase):
    status: str | None = Field(default=None, description="search by lesson status")
    custom_status: str | None = Field(default=None, description="search by lesson custom status")
    student_id: int | None = Field(default=None, description="search by student id")
    lesson_id: int | None = Field(default=None, description="search by lesson id")
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class LocationListParams(ListParamsBase):
    name: str | None = Field(default=None, description="search by name")
    parent_location_id: int | None = Field(
        default=None,
        description="search by parent location id if location is a sub-location",
    )
    state: str | None = Field(default=None, description="search by state")
    zip: str | None = Field(default=None, description="search by zip")
    id_gt: int | None = Field(
        default=None,
        serialization_alias="id[gt]",
        description="search where id is greater than",
    )
    id_lt: int | None = Field(
        default=None,
        serialization_alias="id[lt]",
        description="search where id is less than",
    )
    id_gte: int | None = Field(
        default=None,
        serialization_alias="id[gte]",
        description="search where id is equal to or greater than",
    )
    id_lte: int | None = Field(
        default=None,
        serialization_alias="id[lte]",
        description="search where id is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class OtherCompensationListParams(ListParamsBase):
    employee_id: int | None = Field(default=None, description="search by employee id")
    date: Date | None = Field(
        default=None,
        description="search by compensation date. Use YYYY-MM-DD format.",
    )
    date_gt: Date | None = Field(
        default=None,
        serialization_alias="date[gt]",
        description="search where date is greater than",
    )
    date_lt: Date | None = Field(
        default=None,
        serialization_alias="date[lt]",
        description="search where date is less than",
    )
    date_gte: Date | None = Field(
        default=None,
        serialization_alias="date[gte]",
        description="search where date is equal to or greater than",
    )
    date_lte: Date | None = Field(
        default=None,
        serialization_alias="date[lte]",
        description="search where date is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class OtherEventListParams(ListParamsBase):
    series_id: int | None = Field(
        default=None,
        description="search by series id for repeating events",
    )
    location_id: int | None = Field(default=None, description="search by location id")
    employee_id: int | None = Field(default=None, description="search by employee id")
    from_date: Date | None = Field(
        default=None,
        description="search by date the event starts on. Use YYYY-MM-DD format.",
    )
    from_date_gt: Date | None = Field(
        default=None,
        serialization_alias="from_date[gt]",
        description="search where date is greater than",
    )
    from_date_lt: Date | None = Field(
        default=None,
        serialization_alias="from_date[lt]",
        description="search where date is less than",
    )
    from_date_gte: Date | None = Field(
        default=None,
        serialization_alias="from_date[gte]",
        description="search where date is equal to or greater than",
    )
    from_date_lte: Date | None = Field(
        default=None,
        serialization_alias="from_date[lte]",
        description="search where date is equal to or less than",
    )
    to_date: Date | None = Field(
        default=None,
        description="search by date the event ends on. Use YYYY-MM-DD format.",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class PaymentAllocationListParams(ListParamsBase):
    payment_id: int | None = Field(default=None, description="search by payment id")
    invoice_id: int | None = Field(default=None, description="search by invoice id")
    date: Date | None = Field(
        default=None,
        description="search by payment date. Use YYYY-MM-DD format.",
    )
    date_gt: Date | None = Field(
        default=None,
        serialization_alias="date[gt]",
        description="search where date is greater than",
    )
    date_lt: Date | None = Field(
        default=None,
        serialization_alias="date[lt]",
        description="search where date is less than",
    )
    date_gte: Date | None = Field(
        default=None,
        serialization_alias="date[gte]",
        description="search where date is equal to or greater than",
    )
    date_lte: Date | None = Field(
        default=None,
        serialization_alias="date[lte]",
        description="search where date is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class PaymentListParams(ListParamsBase):
    customer_id: int | None = Field(default=None, description="search by customer id")
    date: Date | None = Field(
        default=None,
        description="search by payment date. Use YYYY-MM-DD format.",
    )
    date_gt: Date | None = Field(
        default=None,
        serialization_alias="date[gt]",
        description="search where date is greater than",
    )
    date_lt: Date | None = Field(
        default=None,
        serialization_alias="date[lt]",
        description="search where date is less than",
    )
    date_gte: Date | None = Field(
        default=None,
        serialization_alias="date[gte]",
        description="search where date is equal to or greater than",
    )
    date_lte: Date | None = Field(
        default=None,
        serialization_alias="date[lte]",
        description="search where date is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class RepertoireListParams(ListParamsBase):
    student_id: int | None = Field(
        default=None,
        description="If provided, it will filter the result set by the given id of a student.",
    )
    sort_direction: str | None = Field(
        default=None,
        description="Values can be asc for ascending order or desc for descending order.",
    )


class ResultGroupListParams(ListParamsBase):
    name: str | None = Field(default=None, description="search by name")
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class ResultListParams(ListParamsBase):
    student_id: int | None = Field(default=None, description="search by student id")
    result_group_id: int | None = Field(default=None, description="search by result group id")
    date: Date | None = Field(
        default=None,
        description="search by result date. Use YYYY-MM-DD format.",
    )
    date_gt: Date | None = Field(
        default=None,
        serialization_alias="date[gt]",
        description="search where date is greater than",
    )
    date_lt: Date | None = Field(
        default=None,
        serialization_alias="date[lt]",
        description="search where date is less than",
    )
    date_gte: Date | None = Field(
        default=None,
        serialization_alias="date[gte]",
        description="search where date is equal to or greater than",
    )
    date_lte: Date | None = Field(
        default=None,
        serialization_alias="date[lte]",
        description="search where date is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class ServiceListParams(ListParamsBase):
    name: str | None = Field(default=None, description="search by name")
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class StudentGroupListParams(ListParamsBase):
    name: str | None = Field(
        default=None,
        description="search by name (will return partial matches)",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class StudentListParams(ListParamsBase):
    customer_id: int | None = Field(default=None, description="search by customer id")
    first_name: str | None = Field(default=None, description="search by first name")
    last_name: str | None = Field(default=None, description="search by last name")
    email: str | None = Field(default=None, description="search by email")
    phone_number: str | None = Field(default=None, description="search by phone number")
    school: str | None = Field(default=None, description="search by school")
    grade: str | None = Field(default=None, description="search by grade")
    subject: str | None = Field(default=None, description="search by subject")
    type_: str | None = Field(
        default=None,
        serialization_alias="type",
        description="search by customer type (family or independent)",
    )
    status: str | None = Field(
        default=None,
        description="search by status (Active, Inactive, Prospective)",
    )
    id_gt: int | None = Field(
        default=None,
        serialization_alias="id[gt]",
        description="search where id is greater than",
    )
    id_lt: int | None = Field(
        default=None,
        serialization_alias="id[lt]",
        description="search where id is less than",
    )
    id_gte: int | None = Field(
        default=None,
        serialization_alias="id[gte]",
        description="search where id is equal to or greater than",
    )
    id_lte: int | None = Field(
        default=None,
        serialization_alias="id[lte]",
        description="search where id is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class SubjectListParams(ListParamsBase):
    name: str | None = Field(
        default=None,
        description="search by name (will return partial matches)",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class UnavailabilityListParams(ListParamsBase):
    employee_id: int | None = Field(default=None, description="search by employee id")
    series_id: int | None = Field(
        default=None,
        description="search by series id for repeating lessons",
    )
    from_date: Date | None = Field(
        default=None,
        description="search by date the unavailability starts on. Use YYYY-MM-DD format.",
    )
    from_date_gt: Date | None = Field(
        default=None,
        serialization_alias="from_date[gt]",
        description="search where start date is greater than",
    )
    from_date_lt: Date | None = Field(
        default=None,
        serialization_alias="from_date[lt]",
        description="search where start date is less than",
    )
    from_date_gte: Date | None = Field(
        default=None,
        serialization_alias="from_date[gte]",
        description="search where start date is equal to or greater than",
    )
    from_date_lte: Date | None = Field(
        default=None,
        serialization_alias="from_date[lte]",
        description="search where start date is equal to or less than",
    )
    to_date: Date | None = Field(
        default=None,
        description="search by date the unavailability ends on. Use YYYY-MM-DD format.",
    )
    to_date_gt: Date | None = Field(
        default=None,
        serialization_alias="to_date[gt]",
        description="search where end date is greater than",
    )
    to_date_lt: Date | None = Field(
        default=None,
        serialization_alias="to_date[lt]",
        description="search where end date is less than",
    )
    to_date_gte: Date | None = Field(
        default=None,
        serialization_alias="to_date[gte]",
        description="search where end date is equal to or greater than",
    )
    to_date_lte: Date | None = Field(
        default=None,
        serialization_alias="to_date[lte]",
        description="search where end date is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class WagePaymentListParams(ListParamsBase):
    employee_id: int | None = Field(default=None, description="search by employee id")
    date: Date | None = Field(
        default=None,
        description="search by wage payment date. Use YYYY-MM-DD format.",
    )
    date_gt: Date | None = Field(
        default=None,
        serialization_alias="date[gt]",
        description="search where date is greater than",
    )
    date_lt: Date | None = Field(
        default=None,
        serialization_alias="date[lt]",
        description="search where date is less than",
    )
    date_gte: Date | None = Field(
        default=None,
        serialization_alias="date[gte]",
        description="search where date is equal to or greater than",
    )
    date_lte: Date | None = Field(
        default=None,
        serialization_alias="date[lte]",
        description="search where date is equal to or less than",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )


class WageTierListParams(ListParamsBase):
    name: str | None = Field(default=None, description="search by name")
    service_id: int | None = Field(
        default=None,
        description="search by the id of the service that this wage tier is associated with",
    )
    direction: str | None = Field(
        default=None,
        description="direction to sort by primary id (asc, desc), defaults to asc",
    )
