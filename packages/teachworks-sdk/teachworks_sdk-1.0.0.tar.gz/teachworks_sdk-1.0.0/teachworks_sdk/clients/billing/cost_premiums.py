from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from teachworks_sdk.models import CostPremium, CostPremiumListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class CostPremiumsClient:
    """Client for Teachworks cost premium endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the cost premiums client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, cost_premium_id: int) -> CostPremium:
        """Retrieve a cost premium by ID.

        :param cost_premium_id: Cost premium identifier.
        :type cost_premium_id: int
        :returns: The requested cost premium.
        :rtype: CostPremium
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/cost_premiums", CostPremium, cost_premium_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: CostPremiumListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[CostPremium]:
        """List cost premiums with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: CostPremiumListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of cost premiums.
        :rtype: list[CostPremium]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/cost_premiums",
            CostPremium,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )
