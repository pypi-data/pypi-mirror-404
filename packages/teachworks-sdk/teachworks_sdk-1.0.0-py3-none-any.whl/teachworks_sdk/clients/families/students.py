from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import TypeAdapter

from teachworks_sdk.logging_utils import get_logger
from teachworks_sdk.models import (
    CustomFieldUpdateItem,
    CustomFieldUpdateResponse,
    Student,
    StudentListParams,
    StudentLessonTotals,
)

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class StudentsClient:
    """Client for Teachworks student endpoints."""

    def __init__(self, session: TeachworksSession, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the students client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        :param logger: Custom logger instance. If None, uses default SDK logger.
        :type logger: logging.Logger | None
        """
        self._session = session
        self.logger = logger or get_logger("clients.students")

    def retrieve(self, student_id: int) -> Student:
        """Retrieve a student by ID.

        :param student_id: Student identifier.
        :type student_id: int
        :returns: The requested student.
        :rtype: Student
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/students", Student, student_id)

    def retrieve_lesson_totals(self, student_id: int) -> StudentLessonTotals:
        """Retrieve lesson totals for a student.

        :param student_id: Student identifier.
        :type student_id: int
        :returns: Student lesson totals.
        :rtype: StudentLessonTotals
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("GET", f"/students/{student_id}/lesson_totals")
        return self._session._parse_model(StudentLessonTotals, data)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: StudentListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[Student]:
        """List students with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: StudentListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of students.
        :rtype: list[Student]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/students",
            Student,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def create_child(self, payload: Dict[str, Any]) -> Student:
        """Create a child student (associated with a family).

        :param payload: Student payload.
        :type payload: dict[str, Any]
        :returns: Created student.
        :rtype: Student
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        self.logger.info("Creating child student")
        data = self._session._request("POST", "/students", payload=payload)
        student = self._session._parse_model(Student, data)
        self.logger.info("Created child student (id=%d)", student.id)
        return student

    def create_independent(self, payload: Dict[str, Any]) -> Student:
        """Create an independent student.

        :param payload: Student payload.
        :type payload: dict[str, Any]
        :returns: Created student.
        :rtype: Student
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        self.logger.info("Creating independent student")
        data = self._session._request("POST", "/students/independent_student", payload=payload)
        student = self._session._parse_model(Student, data)
        self.logger.info("Created independent student (id=%d)", student.id)
        return student

    def set_custom_fields(
        self,
        student_id: int,
        payload: list[CustomFieldUpdateItem],
    ) -> CustomFieldUpdateResponse:
        """Set student custom field values.

        :param student_id: Student identifier.
        :type student_id: int
        :param payload: Custom field payload.
        :type payload: list[CustomFieldUpdateItem]
        :returns: Custom field update response.
        :rtype: CustomFieldUpdateResponse
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        self.logger.info("Setting custom fields for student (id=%d)", student_id)
        adapter = TypeAdapter(list[CustomFieldUpdateItem])
        items = adapter.validate_python(payload)
        data = self._session._request(
            "PUT",
            f"/students/{student_id}/custom_fields",
            payload={"custom_fields": [item.model_dump() for item in items]},
        )
        response = self._session._parse_model(CustomFieldUpdateResponse, data)
        self.logger.info("Successfully set custom fields for student (id=%d)", student_id)
        return response

    def update_child(self, student_id: int, payload: Dict[str, Any]) -> Student:
        """Update a child student.

        :param student_id: Student identifier.
        :type student_id: int
        :param payload: Update payload.
        :type payload: dict[str, Any]
        :returns: Updated student.
        :rtype: Student
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("PUT", f"/students/{student_id}", payload=payload)
        return self._session._parse_model(Student, data)

    def update_independent(self, student_id: int, payload: Dict[str, Any]) -> Student:
        """Update an independent student.

        :param student_id: Student identifier.
        :type student_id: int
        :param payload: Update payload.
        :type payload: dict[str, Any]
        :returns: Updated student.
        :rtype: Student
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("PUT", f"/students/{student_id}", payload=payload)
        return self._session._parse_model(Student, data)
