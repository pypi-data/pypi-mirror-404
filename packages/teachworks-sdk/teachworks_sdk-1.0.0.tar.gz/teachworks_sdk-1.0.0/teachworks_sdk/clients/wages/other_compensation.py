from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from teachworks_sdk.models import OtherCompensation, OtherCompensationListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class OtherCompensationClient:
    """Client for Teachworks other compensation endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the other compensation client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, compensation_id: int) -> OtherCompensation:
        """Retrieve other compensation by ID.

        :param compensation_id: Compensation identifier.
        :type compensation_id: int
        :returns: The requested compensation.
        :rtype: OtherCompensation
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/other_compensation", OtherCompensation, compensation_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: OtherCompensationListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[OtherCompensation]:
        """List other compensation with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: OtherCompensationListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of other compensation records.
        :rtype: list[OtherCompensation]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/other_compensation",
            OtherCompensation,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def create(self, payload: Dict[str, Any]) -> OtherCompensation:
        """Create other compensation.

        :param payload: Compensation payload.
        :type payload: dict[str, Any]
        :returns: Created compensation record.
        :rtype: OtherCompensation
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("POST", "/other_compensation", payload=payload)
        return self._session._parse_model(OtherCompensation, data)
