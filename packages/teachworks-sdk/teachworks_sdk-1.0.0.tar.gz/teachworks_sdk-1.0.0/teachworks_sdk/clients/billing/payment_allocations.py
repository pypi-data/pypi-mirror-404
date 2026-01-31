from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from teachworks_sdk.models import PaymentAllocation, PaymentAllocationListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class PaymentAllocationsClient:
    """Client for Teachworks payment allocation endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the payment allocations client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, allocation_id: int) -> PaymentAllocation:
        """Retrieve a payment allocation by ID.

        :param allocation_id: Allocation identifier.
        :type allocation_id: int
        :returns: The requested payment allocation.
        :rtype: PaymentAllocation
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/payment_allocations", PaymentAllocation, allocation_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: PaymentAllocationListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[PaymentAllocation]:
        """List payment allocations with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: PaymentAllocationListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of payment allocations.
        :rtype: list[PaymentAllocation]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/payment_allocations",
            PaymentAllocation,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def create(self, payload: Dict[str, Any]) -> PaymentAllocation:
        """Create a payment allocation.

        :param payload: Allocation payload.
        :type payload: dict[str, Any]
        :returns: Created payment allocation.
        :rtype: PaymentAllocation
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("POST", "/payment_allocations", payload=payload)
        return self._session._parse_model(PaymentAllocation, data)
