from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import TypeAdapter

from teachworks_sdk.models import (
    CustomFieldUpdateItem,
    CustomFieldUpdateResponse,
    Customer,
    CustomerListParams,
    CustomerLessonTotals,
)

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class CustomersClient:
    """Client for Teachworks customer endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the customers client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, customer_id: int) -> Customer:
        """Retrieve a customer by ID.

        :param customer_id: Customer identifier.
        :type customer_id: int
        :returns: The requested customer.
        :rtype: Customer
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/customers", Customer, customer_id)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: CustomerListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[Customer]:
        """List customers with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: CustomerListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of customers.
        :rtype: list[Customer]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/customers",
            Customer,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def retrieve_lesson_totals(self, customer_id: int) -> CustomerLessonTotals:
        """Retrieve lesson totals for a customer.

        :param customer_id: Customer identifier.
        :type customer_id: int
        :returns: Customer lesson totals.
        :rtype: CustomerLessonTotals
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("GET", f"/customers/{customer_id}/lesson_totals")
        return self._session._parse_model(CustomerLessonTotals, data)

    def create_family(self, payload: Dict[str, Any]) -> Customer:
        """Create a family customer.

        :param payload: Family payload matching Teachworks API parameters.
        :type payload: dict[str, Any]
        :returns: Created family customer.
        :rtype: Customer
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("POST", "/customers/family", payload=payload)
        return self._session._parse_model(Customer, data)

    def create_independent_student(self, payload: Dict[str, Any]) -> Customer:
        """Create an independent student customer.

        :param payload: Independent student payload.
        :type payload: dict[str, Any]
        :returns: Created customer record.
        :rtype: Customer
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("POST", "/customers/independent_student", payload=payload)
        return self._session._parse_model(Customer, data)

    def set_custom_fields(
        self,
        customer_id: int,
        payload: list[CustomFieldUpdateItem],
    ) -> CustomFieldUpdateResponse:
        """Set customer custom field values.

        :param customer_id: Customer identifier.
        :type customer_id: int
        :param payload: Custom field payload.
        :type payload: list[CustomFieldUpdateItem]
        :returns: Custom field update response.
        :rtype: CustomFieldUpdateResponse
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        adapter = TypeAdapter(list[CustomFieldUpdateItem])
        items = adapter.validate_python(payload)
        data = self._session._request(
            "PUT",
            f"/customers/{customer_id}/custom_fields",
            payload={"custom_fields": [item.model_dump() for item in items]},
        )
        return self._session._parse_model(CustomFieldUpdateResponse, data)

    def update_family(self, customer_id: int, payload: Dict[str, Any]) -> Customer:
        """Update a family customer.

        :param customer_id: Customer identifier.
        :type customer_id: int
        :param payload: Update payload.
        :type payload: dict[str, Any]
        :returns: Updated customer.
        :rtype: Customer
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("PUT", f"/customers/{customer_id}", payload=payload)
        return self._session._parse_model(Customer, data)

    def update_independent_student(self, customer_id: int, payload: Dict[str, Any]) -> Customer:
        """Update an independent student customer.

        :param customer_id: Customer identifier.
        :type customer_id: int
        :param payload: Update payload.
        :type payload: dict[str, Any]
        :returns: Updated customer.
        :rtype: Customer
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("PUT", f"/customers/{customer_id}", payload=payload)
        return self._session._parse_model(Customer, data)
