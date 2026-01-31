"""Resolver helpers for Teachworks model relationships."""

from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar, TYPE_CHECKING, Optional

from teachworks_sdk.logging_utils import get_logger
from teachworks_sdk.models.base import TeachworksBaseModel
from teachworks_sdk.models.resources import (
    Availability,
    CreditNoteAllocation,
    Customer,
    Employee,
    Invoice,
    Lesson,
    LessonParticipant,
    Location,
    OtherCompensation,
    Payment,
    PaymentAllocation,
    Repertoire,
    Result,
    ResultGroup,
    Service,
    Student,
    Unavailability,
    WagePayment,
    WageTier,
)

if TYPE_CHECKING:
    from teachworks_sdk.models.resources import CostPremium
    from teachworks_sdk.session import TeachworksSession

ModelT = TypeVar("ModelT", bound=TeachworksBaseModel)


class BaseResolver(Generic[ModelT]):
    """Bind a model instance to a session for explicit relationship lookup."""

    def __init__(self, model: ModelT, session: TeachworksSession, logger: Optional[logging.Logger] = None) -> None:
        self._model = model
        self._session = session
        self.logger = logger or get_logger("models.resolvers")
        self.logger.debug(
            "Resolver initialized for %s(id=%s)",
            type(model).__name__,
            getattr(model, "id", None),
        )

    @property
    def model(self) -> ModelT:
        """Return the bound model instance."""
        return self._model


class LessonParticipantResolver(BaseResolver[LessonParticipant]):
    """Resolver for lesson participant relationships."""

    def student(self) -> Student:
        """Resolve the student for this participant."""
        self.logger.debug(
            "Resolving student (id=%d) for LessonParticipant(id=%d)",
            self._model.student_id,
            self._model.id,
        )
        return self._session.students.retrieve(self._model.student_id)

    def lesson(self) -> Lesson:
        """Resolve the lesson for this participant."""
        self.logger.debug(
            "Resolving lesson (id=%d) for LessonParticipant(id=%d)",
            self._model.lesson_id,
            self._model.id,
        )
        return self._session.lessons.retrieve(self._model.lesson_id)


class LessonResolver(BaseResolver[Lesson]):
    """Resolver for lesson relationships."""

    def service(self) -> Service:
        """Resolve the service for this lesson."""
        return self._session.services.retrieve(self._model.service_id)

    def employee(self) -> Employee:
        """Resolve the employee (tutor) for this lesson."""
        return self._session.employees.retrieve(self._model.employee_id)

    def location(self) -> Location:
        """Resolve the location for this lesson."""
        return self._session.locations.retrieve(self._model.location_id)

    def request_customer(self) -> Customer | None:
        """Resolve the requested customer for this lesson."""
        if self._model.request_customer_id is None:
            return None
        return self._session.customers.retrieve(self._model.request_customer_id)

    def request_student(self) -> Student | None:
        """Resolve the requested student for this lesson."""
        if self._model.request_student_id is None:
            return None
        return self._session.students.retrieve(self._model.request_student_id)


class StudentResolver(BaseResolver[Student]):
    """Resolver for student relationships."""

    def customer(self) -> Customer:
        """Resolve the customer (family) for this student."""
        return self._session.customers.retrieve(self._model.customer_id)

    def cost_premium(self) -> CostPremium | None:
        """Resolve the cost premium for this student."""
        if self._model.cost_premium_id is None:
            return None
        from teachworks_sdk.models.resources import CostPremium

        return self._session.cost_premiums.retrieve(self._model.cost_premium_id)

    def default_location(self) -> Location | None:
        """Resolve the default location for this student."""
        if self._model.default_location_id is None:
            return None
        return self._session.locations.retrieve(self._model.default_location_id)


class CustomerResolver(BaseResolver[Customer]):
    """Resolver for customer relationships."""

    def family_customer(self) -> Customer | None:
        """Resolve the family customer record for this customer."""
        if self._model.family_customer_id is None:
            return None
        return self._session.customers.retrieve(self._model.family_customer_id)


class EmployeeResolver(BaseResolver[Employee]):
    """Resolver for employee relationships."""

    def wage_tier(self) -> WageTier | None:
        """Resolve the wage tier for this employee."""
        if self._model.wage_tier_id is None:
            return None
        return self._session.wage_tiers.retrieve(self._model.wage_tier_id)


class AvailabilityResolver(BaseResolver[Availability]):
    """Resolver for availability relationships."""

    def employee(self) -> Employee:
        """Resolve the employee for this availability."""
        return self._session.employees.retrieve(self._model.employee_id)


class UnavailabilityResolver(BaseResolver[Unavailability]):
    """Resolver for unavailability relationships."""

    def employee(self) -> Employee:
        """Resolve the employee for this unavailability."""
        return self._session.employees.retrieve(self._model.employee_id)


class InvoiceResolver(BaseResolver[Invoice]):
    """Resolver for invoice relationships."""

    def customer(self) -> Customer:
        """Resolve the customer for this invoice."""
        return self._session.customers.retrieve(self._model.customer_id)


class PaymentResolver(BaseResolver[Payment]):
    """Resolver for payment relationships."""

    def customer(self) -> Customer:
        """Resolve the customer for this payment."""
        return self._session.customers.retrieve(self._model.customer_id)


class PaymentAllocationResolver(BaseResolver[PaymentAllocation]):
    """Resolver for payment allocation relationships."""

    def payment(self) -> Payment:
        """Resolve the payment for this allocation."""
        return self._session.payments.retrieve(self._model.payment_id)

    def invoice(self) -> Invoice:
        """Resolve the invoice for this allocation."""
        return self._session.invoices.retrieve(self._model.invoice_id)


class CreditNoteAllocationResolver(BaseResolver[CreditNoteAllocation]):
    """Resolver for credit note allocation relationships."""

    def invoice(self) -> Invoice:
        """Resolve the invoice for this allocation."""
        return self._session.invoices.retrieve(self._model.invoice_id)


class OtherCompensationResolver(BaseResolver[OtherCompensation]):
    """Resolver for other compensation relationships."""

    def employee(self) -> Employee:
        """Resolve the employee for this compensation."""
        return self._session.employees.retrieve(self._model.employee_id)


class WagePaymentResolver(BaseResolver[WagePayment]):
    """Resolver for wage payment relationships."""

    def employee(self) -> Employee:
        """Resolve the employee for this wage payment."""
        return self._session.employees.retrieve(self._model.employee_id)


class ResultResolver(BaseResolver[Result]):
    """Resolver for result relationships."""

    def student(self) -> Student:
        """Resolve the student for this result."""
        return self._session.students.retrieve(self._model.student_id)

    def result_group(self) -> ResultGroup:
        """Resolve the result group for this result."""
        return self._session.result_groups.retrieve(self._model.result_group_id)


class RepertoireResolver(BaseResolver[Repertoire]):
    """Resolver for repertoire relationships."""

    def student(self) -> Student:
        """Resolve the student for this repertoire item."""
        return self._session.students.retrieve(self._model.student_id)


def get_resolver_for(model: TeachworksBaseModel, session: TeachworksSession) -> BaseResolver[Any]:
    """Return the appropriate resolver for a given model."""
    if isinstance(model, LessonParticipant):
        return LessonParticipantResolver(model, session)
    if isinstance(model, Lesson):
        return LessonResolver(model, session)
    if isinstance(model, Student):
        return StudentResolver(model, session)
    if isinstance(model, Customer):
        return CustomerResolver(model, session)
    if isinstance(model, Employee):
        return EmployeeResolver(model, session)
    if isinstance(model, Availability):
        return AvailabilityResolver(model, session)
    if isinstance(model, Unavailability):
        return UnavailabilityResolver(model, session)
    if isinstance(model, Invoice):
        return InvoiceResolver(model, session)
    if isinstance(model, Payment):
        return PaymentResolver(model, session)
    if isinstance(model, PaymentAllocation):
        return PaymentAllocationResolver(model, session)
    if isinstance(model, CreditNoteAllocation):
        return CreditNoteAllocationResolver(model, session)
    if isinstance(model, OtherCompensation):
        return OtherCompensationResolver(model, session)
    if isinstance(model, WagePayment):
        return WagePaymentResolver(model, session)
    if isinstance(model, Result):
        return ResultResolver(model, session)
    if isinstance(model, Repertoire):
        return RepertoireResolver(model, session)
    return BaseResolver(model, session)
