from __future__ import annotations

from typing import TYPE_CHECKING, List

from teachworks_sdk.models import Service, ServiceListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class ServicesClient:
    """Client for Teachworks service endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the services client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, service_id: int) -> Service:
        """Retrieve a service by ID.

        :param service_id: Service identifier.
        :type service_id: int
        :returns: The requested service.
        :rtype: Service
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/services", Service, service_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: ServiceListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[Service]:
        """List services with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: ServiceListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of services.
        :rtype: list[Service]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/services",
            Service,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )
