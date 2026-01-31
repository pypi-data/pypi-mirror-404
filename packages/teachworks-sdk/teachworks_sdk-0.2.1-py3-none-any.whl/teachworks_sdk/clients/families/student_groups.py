from __future__ import annotations

from typing import TYPE_CHECKING, List

from teachworks_sdk.models import StudentGroup, StudentGroupListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class StudentGroupsClient:
    """Client for Teachworks student group endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the student groups client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, group_id: int) -> StudentGroup:
        """Retrieve a student group by ID.

        :param group_id: Student group identifier.
        :type group_id: int
        :returns: The requested student group.
        :rtype: StudentGroup
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/student_groups", StudentGroup, group_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: StudentGroupListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[StudentGroup]:
        """List student groups with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: StudentGroupListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of student groups.
        :rtype: list[StudentGroup]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/student_groups",
            StudentGroup,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )
