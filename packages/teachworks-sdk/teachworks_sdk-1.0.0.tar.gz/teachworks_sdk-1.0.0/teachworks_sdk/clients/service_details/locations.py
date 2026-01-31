from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from teachworks_sdk.models import Location, LocationListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class LocationsClient:
    """Client for Teachworks location endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the locations client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, location_id: int) -> Location:
        """Retrieve a single location by ID.

        :param location_id: Location identifier.
        :type location_id: int
        :returns: The requested location.
        :rtype: Location
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/locations", Location, location_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: LocationListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[Location]:
        """List locations with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: LocationListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of locations.
        :rtype: list[Location]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/locations",
            Location,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def create(self, payload: Dict[str, Any]) -> Location:
        """Create a new location.

        :param payload: Location payload matching Teachworks API parameters.
        :type payload: dict[str, Any]
        :returns: Created location.
        :rtype: Location
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("POST", "/locations", payload=payload)
        return self._session._parse_model(Location, data)

    def update(self, location_id: int, payload: Dict[str, Any]) -> Location:
        """Update an existing location.

        :param location_id: Location identifier.
        :type location_id: int
        :param payload: Update payload matching Teachworks API parameters.
        :type payload: dict[str, Any]
        :returns: Updated location.
        :rtype: Location
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("PUT", f"/locations/{location_id}", payload=payload)
        return self._session._handle_update_response(Location, location_id, data)
