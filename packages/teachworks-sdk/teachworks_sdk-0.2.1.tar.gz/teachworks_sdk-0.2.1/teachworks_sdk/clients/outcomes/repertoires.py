"""API resource clients for Teachworks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from teachworks_sdk.models import Repertoire, RepertoireListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class RepertoiresClient:
    """Client for Teachworks repertoire endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the repertoire client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: RepertoireListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[Repertoire]:
        """List repertoires with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: RepertoireListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of repertoires.
        :rtype: list[Repertoire]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/repertoires",
            Repertoire,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def retrieve(self, repertoire_id: int) -> Repertoire:
        """Retrieve a repertoire by ID.

        :param repertoire_id: Repertoire identifier.
        :type repertoire_id: int
        :returns: The requested repertoire.
        :rtype: Repertoire
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/repertoires", Repertoire, repertoire_id)

    def create(self, payload: Dict[str, Any]) -> Repertoire:
        """Create a repertoire.

        :param payload: Repertoire payload.
        :type payload: dict[str, Any]
        :returns: Created repertoire.
        :rtype: Repertoire
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("POST", "/repertoires", payload=payload)
        return self._session._parse_model(Repertoire, data)
