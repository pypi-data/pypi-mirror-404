from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from teachworks_sdk.models import ResultGroup, ResultGroupListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class ResultGroupsClient:
    """Client for Teachworks result group endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the result groups client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, result_group_id: int) -> ResultGroup:
        """Retrieve a result group by ID.

        :param result_group_id: Result group identifier.
        :type result_group_id: int
        :returns: The requested result group.
        :rtype: ResultGroup
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/result_groups", ResultGroup, result_group_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: ResultGroupListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[ResultGroup]:
        """List result groups with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: ResultGroupListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of result groups.
        :rtype: list[ResultGroup]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/result_groups",
            ResultGroup,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )
