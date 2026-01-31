from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from teachworks_sdk.logging_utils import get_logger
from teachworks_sdk.models import Lesson, LessonListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class LessonsClient:
    """Client for Teachworks lesson endpoints."""

    def __init__(self, session: TeachworksSession, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the lessons client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        :param logger: Custom logger instance. If None, uses default SDK logger.
        :type logger: logging.Logger | None
        """
        self._session = session
        self.logger = logger or get_logger("clients.lessons")

    def retrieve(self, lesson_id: int) -> Lesson:
        """Retrieve a lesson by ID.

        :param lesson_id: Lesson identifier.
        :type lesson_id: int
        :returns: The requested lesson.
        :rtype: Lesson
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/lessons", Lesson, lesson_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: LessonListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[Lesson]:
        """List lessons with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: LessonListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of lessons.
        :rtype: list[Lesson]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/lessons",
            Lesson,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def create(self, payload: Dict[str, Any]) -> Lesson:
        """Create a new lesson.

        :param payload: Lesson payload.
        :type payload: dict[str, Any]
        :returns: Created lesson.
        :rtype: Lesson
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        self.logger.info("Creating lesson")
        data = self._session._request("POST", "/lessons", payload=payload)
        lesson = self._session._parse_model(Lesson, data)
        self.logger.info("Created lesson (id=%d)", lesson.id)
        return lesson

    def add_student(self, lesson_id: int, payload: Dict[str, Any]) -> Lesson:
        """Add a student to a lesson.

        :param lesson_id: Lesson identifier.
        :type lesson_id: int
        :param payload: Participant payload.
        :type payload: dict[str, Any]
        :returns: Updated lesson.
        :rtype: Lesson
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        student_id = payload.get("student_id")
        self.logger.info("Adding student (student_id=%s) to lesson (id=%d)", student_id, lesson_id)
        data = self._session._request("PUT", f"/lessons/{lesson_id}/add_student", payload=payload)
        lesson = self._session._parse_model(Lesson, data)
        self.logger.info("Successfully added student to lesson (id=%d)", lesson_id)
        return lesson

    def complete(self, lesson_id: int, payload: Dict[str, Any]) -> Lesson:
        """Complete a lesson.

        :param lesson_id: Lesson identifier.
        :type lesson_id: int
        :param payload: Completion payload.
        :type payload: dict[str, Any]
        :returns: Updated lesson.
        :rtype: Lesson
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        self.logger.info("Completing lesson (id=%d)", lesson_id)
        data = self._session._request("PUT", f"/lessons/{lesson_id}/complete", payload=payload)
        lesson = self._session._parse_model(Lesson, data)
        self.logger.info("Successfully completed lesson (id=%d)", lesson_id)
        return lesson
