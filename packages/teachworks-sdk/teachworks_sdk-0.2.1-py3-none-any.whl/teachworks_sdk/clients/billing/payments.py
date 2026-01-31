from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from teachworks_sdk.models import Payment, PaymentListParams

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class PaymentsClient:
    """Client for Teachworks payment endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the payments client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, payment_id: int) -> Payment:
        """Retrieve a payment by ID.

        :param payment_id: Payment identifier.
        :type payment_id: int
        :returns: The requested payment.
        :rtype: Payment
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/payments", Payment, payment_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: PaymentListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[Payment]:
        """List payments with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: PaymentListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of payments.
        :rtype: list[Payment]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/payments",
            Payment,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def create(self, payload: Dict[str, Any]) -> Payment:
        """Create a payment.

        :param payload: Payment payload.
        :type payload: dict[str, Any]
        :returns: Created payment.
        :rtype: Payment
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("POST", "/payments", payload=payload)
        return self._session._parse_model(Payment, data)

    def update(self, payment_id: int, payload: Dict[str, Any]) -> Payment:
        """Update a payment.

        :param payment_id: Payment identifier.
        :type payment_id: int
        :param payload: Update payload.
        :type payload: dict[str, Any]
        :returns: Updated payment.
        :rtype: Payment
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("PUT", f"/payments/{payment_id}", payload=payload)
        return self._session._handle_update_response(Payment, payment_id, data)
