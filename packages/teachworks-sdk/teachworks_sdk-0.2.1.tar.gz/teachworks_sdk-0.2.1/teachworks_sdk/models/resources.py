"""Resource models for Teachworks API responses."""

from __future__ import annotations

from datetime import date as Date, datetime, time as Time
from decimal import Decimal
from typing import Any, ClassVar

from pydantic import Field

from teachworks_sdk.models.base import TeachworksBaseModel, LessonTotals


class CustomFieldValue(TeachworksBaseModel):
    field_id: int
    name: str | None = None
    value: Any | None = None
    student_id: int | None = None
    customer_id: int | None = None
    employee_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CustomFieldUpdateItem(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    field_id: int
    value: Any


class CustomFieldUpdateResult(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    field_id: int
    name: str | None = None
    value: Any | None = None
    student_id: int | None = None
    customer_id: int | None = None
    employee_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CustomFieldUpdateResponse(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    errors: list[str] = Field(default_factory=list)
    updated: list[CustomFieldUpdateResult] = Field(default_factory=list)


class StudentAttributes(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    id: int | None = None
    customer_id: int | None = None
    student_type: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    additional_email: str | None = None
    home_phone: str | None = None
    mobile_phone: str | None = None
    birth_date: Date | None = None
    start_date: Date | None = None
    school: str | None = None
    grade: str | None = None
    additional_notes: str | None = None
    calendar_color: str | None = None
    default_location_id: int | None = None
    subjects: str | None = None
    status: str | None = None
    time_zone: str | None = None
    billing_method: str | None = None
    student_cost: Decimal | None = None
    cost_premium_id: int | None = None
    discount_rate: Decimal | None = None
    email_lesson_reminders: int | None = None
    email_lesson_notes: int | None = None
    sms_lesson_reminders: int | None = None
    user_account: int | None = None
    unviewed: bool | None = None
    welcome_sent_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    default_teachers: list["DefaultTeacher"] = Field(default_factory=list)
    default_services: list["DefaultService"] = Field(default_factory=list)


class DefaultService(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    id: int
    name: str | None = None


class DefaultTeacher(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    id: int
    first_name: str | None = None
    last_name: str | None = None


class InvoiceLesson(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    id: int
    student_id: int
    employee_id: int | None = None
    service_id: int
    description: str
    status: str
    custom_status: str | None = None
    invoice_unit_price: Decimal
    invoice_discount_rate: Decimal | None = None
    invoice_amount: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaymentAllocationEmbedded(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    id: int
    invoice_id: int
    date: Date | None = None
    amount: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Performance(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    id: int
    event: str
    date: Date | None = None
    grade: str | None = None
    comments: str | None = None


class ServiceWageTier(TeachworksBaseModel):
    __cacheable__: ClassVar[bool] = False

    service_id: int
    wage_tier_id: int
    amount: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Availability(TeachworksBaseModel):
    id: int
    employee_id: int
    day: str
    start_time: Time | None = None
    end_time: Time | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CostPremium(TeachworksBaseModel):
    id: int
    name: str
    amount: Decimal
    wage_amount: Decimal
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreditNoteAllocation(TeachworksBaseModel):
    id: int
    credit_note_id: int
    invoice_id: int
    amount: Decimal
    date: Date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Customer(TeachworksBaseModel):
    id: int
    first_name: str
    last_name: str
    customer_type: str
    status: str
    email: str | None = None
    mobile_phone: str | None = None
    home_phone: str | None = None
    work_phone: str | None = None
    address: str | None = None
    address_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    salutation: str | None = None
    additional_email: str | None = None
    additional_notes: str | None = None
    family_customer_id: int | None = None
    is_family_contact: bool | None = None
    email_lesson_reminders: int | None = None
    sms_lesson_reminders: int | None = None
    email_lesson_notes: int | None = None
    stripe_id: str | None = None
    time_zone: str | None = None
    last_invoice_date: Date | None = None
    welcome_sent_at: datetime | None = None
    user_account: int | None = None
    unviewed: bool | None = None
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    students_attributes: StudentAttributes | list[StudentAttributes] | None = None
    errors: list[str] = Field(default_factory=list)
    updated: list[CustomFieldUpdateResult] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CustomerLessonTotals(LessonTotals):
    customer_id: int


class Employee(TeachworksBaseModel):
    id: int
    first_name: str
    last_name: str
    employee_type: str
    status: str
    email: str | None = None
    mobile_phone: str | None = None
    home_phone: str | None = None
    address: str | None = None
    address_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    hire_date: Date | None = None
    birth_date: Date | None = None
    position: str | None = None
    bio: str | None = None
    calendar_color: str | None = None
    calendar_color_by: str | None = None
    calendar_default_view: str | None = None
    subjects: str | None = None
    wage_type: str | None = None
    work_wage_type: str | None = None
    wage_tier_id: int | None = None
    employee_wage: Decimal | None = None
    work_wage: Decimal | None = None
    include_as_teacher: int | None = None
    sms_lesson_reminders: int | None = None
    email_lesson_reminders: int | None = None
    time_zone: str | None = None
    photo: str | None = None
    user_account: int | None = None
    unviewed: bool | None = None
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    updated: list[CustomFieldUpdateResult] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Permission flags (string booleans in API responses)
    p_accounting: str | None = None
    p_documents: str | None = None
    p_email: str | None = None
    p_employees: str | None = None
    p_event_cost: str | None = None
    p_event_wage: str | None = None
    p_events: str | None = None
    p_events_duration: str | None = None
    p_events_others: str | None = None
    p_integrations: str | None = None
    p_locations: str | None = None
    p_payroll: str | None = None
    p_reports: str | None = None
    p_send_notes: str | None = None
    p_services: str | None = None
    p_settings: str | None = None
    p_staff: str | None = None
    p_student_contact: str | None = None
    p_students: str | None = None
    p_subscription: str | None = None
    p_tasks: str | None = None
    p_teachers: str | None = None


class EmployeeEarnings(TeachworksBaseModel):
    employee_id: int
    lessons: Decimal
    other_events: Decimal
    other_compensation: Decimal
    total: Decimal


class EmployeeLessonTotals(LessonTotals):
    employee_id: int


class Invoice(TeachworksBaseModel):
    id: int
    number: int
    customer_id: int
    customer_first_name: str
    customer_last_name: str
    invoice_type: str
    status: str
    lesson_status: str
    date: Date | None = None
    start_date: Date | None = None
    end_date: Date | None = None
    due_date: Date | None = None
    reference: str
    subtotal: Decimal
    sales_tax_total: Decimal
    total: Decimal
    tax_treatment: str
    hide_flags: bool
    # TODO: Replace with typed models once invoice charge/package payloads are confirmed.
    charges: list[Any] = Field(default_factory=list)
    lessons: list[InvoiceLesson] = Field(default_factory=list)
    packages: list[Any] = Field(default_factory=list)
    sent_at: datetime | None = None
    reminder_sent_at: datetime | None = None
    terms_text: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LessonParticipant(TeachworksBaseModel):
    id: int
    lesson_id: int
    student_id: int
    student_name: str
    status: str
    amount: Decimal
    unit_price: Decimal
    cost_premium_included: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_sent_at: datetime | None = None
    reminder_sent_at: datetime | None = None
    notes_sent_at: datetime | None = None
    family_reminder_sent_at: datetime | None = None
    student_reminder_sent_at: datetime | None = None
    family_sms_sent_at: datetime | None = None
    student_sms_sent_at: datetime | None = None
    discount_rate: Decimal | None = None
    invoice_id: int | None = None
    description: str | None = None
    private_notes: str | None = None
    public_notes: str | None = None
    custom_status: str | None = None
    cost_override_method: str | None = None


class Lesson(TeachworksBaseModel):
    id: int
    name: str
    description: str
    status: str
    service_id: int
    service_name: str
    employee_id: int
    employee_name: str
    location_id: int
    location_name: str
    from_date: Date | None = None
    to_date: Date | None = None
    from_time: Time | None = None
    to_time: Time | None = None
    from_datetime: datetime
    to_datetime: datetime
    duration_minutes: int
    time_zone: str
    wage: Decimal
    participants: list[LessonParticipant] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    cancelled_sent_at: datetime | None = None
    completed_at: datetime | None = None
    reminder_sent_at: datetime | None = None
    sms_sent_at: datetime | None = None
    requested_at: datetime | None = None
    request_comments: str | None = None
    request_customer_id: int | None = None
    request_student_id: int | None = None
    series_id: int | None = None
    joinable: bool | None = None
    parent_location_id: int | None = None
    parent_location_name: str | None = None
    override_method: str | None = None
    override_value: Decimal | None = None
    cost_override: bool | None = None
    custom_status: str | None = None
    spaces: int | None = None
    vehicle_id: int | None = None
    wage_payment_id: int | None = None


class Location(TeachworksBaseModel):
    id: int
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    calendar_color: str | None = None
    spaces: int | None = None
    is_sublocation: bool | None = None
    parent_location_id: int | None = None
    link: str | None = None
    link_enabled: bool | None = None
    display_conflicts: bool | None = None
    exclude_from_location_calendar: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class OtherCompensation(TeachworksBaseModel):
    id: int
    employee_id: int
    employee_first_name: str
    employee_last_name: str
    amount: Decimal
    description: str
    date: Date | None = None
    wage_payment_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

class OtherEvent(TeachworksBaseModel):
    id: int
    name: str
    description: str
    audience: str
    location_id: int
    from_date: Date | None = None
    to_date: Date | None = None
    from_time: Time | None = None
    to_time: Time | None = None
    from_datetime: datetime
    to_datetime: datetime
    duration_minutes: int
    time_zone: str
    # TODO: Confirm other event participant payload shape.
    participants: list[Any] = Field(default_factory=list)
    is_all_day: bool
    series_id: int | None = None
    job_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaymentAllocation(TeachworksBaseModel):
    id: int
    payment_id: int
    invoice_id: int
    amount: Decimal
    date: Date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Payment(TeachworksBaseModel):
    id: int
    customer_id: int
    customer_first_name: str
    customer_last_name: str
    amount: Decimal
    payment_method: str
    type: str
    date: Date | None = None
    description: str
    payment_allocations: list[PaymentAllocationEmbedded] = Field(default_factory=list)
    # TODO: Confirm refund payload shape.
    refunds: list[Any] = Field(default_factory=list)
    sent_at: datetime | None = None
    stripe_transaction_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Repertoire(TeachworksBaseModel):
    id: int
    student_id: int
    student_name: str
    title: str
    composer: str
    genre: str
    source: str
    difficulty: str
    duration: str
    status: str
    date_started: Date | None = None
    date_completed: Date | None = None
    notes: str
    performances: list[Performance] = Field(default_factory=list)
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResultGroup(TeachworksBaseModel):
    id: int
    name: str
    sections: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Result(TeachworksBaseModel):
    id: int
    student_id: int
    student_name: str
    result_group_id: int
    result_group_name: str
    result_group_sections: str
    value: str
    date: Date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Service(TeachworksBaseModel):
    id: int
    name: str
    default_cost: Decimal
    default_wage: Decimal
    archived: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StudentGroup(TeachworksBaseModel):
    id: int
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Student(TeachworksBaseModel):
    id: int
    first_name: str
    last_name: str
    student_type: str
    status: str
    customer_id: int
    calendar_color: str
    billing_method: str
    email: str | None = None
    mobile_phone: str | None = None
    home_phone: str | None = None
    birth_date: Date | None = None
    grade: str | None = None
    school: str | None = None
    cost_premium_id: int | None = None
    default_location_id: int | None = None
    discount_rate: Decimal | None = None
    start_date: Date | None = None
    student_cost: Decimal | None = None
    subjects: str | None = None
    time_zone: str | None = None
    email_lesson_reminders: int | None = None
    sms_lesson_reminders: int | None = None
    email_lesson_notes: int | None = None
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    default_services: list[DefaultService] = Field(default_factory=list)
    default_teachers: list[DefaultTeacher] = Field(default_factory=list)
    user_account: int | None = None
    unviewed: bool | None = None
    additional_email: str | None = None
    additional_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    welcome_sent_at: datetime | None = None
    errors: list[str] = Field(default_factory=list)
    updated: list[CustomFieldUpdateResult] = Field(default_factory=list)


class StudentLessonTotals(LessonTotals):
    student_id: int


class Subject(TeachworksBaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Unavailability(TeachworksBaseModel):
    id: int
    employee_id: int
    description: str
    from_date: Date | None = None
    to_date: Date | None = None
    from_time: Time | None = None
    to_time: Time | None = None
    from_datetime: datetime
    to_datetime: datetime
    time_zone: str
    series_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WagePayment(TeachworksBaseModel):
    id: int
    employee_id: int
    employee_first_name: str
    employee_last_name: str
    amount: Decimal
    date: Date | None = None
    description: str
    sent_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WageTier(TeachworksBaseModel):
    id: int
    name: str
    service_wage_tiers: list[ServiceWageTier] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
