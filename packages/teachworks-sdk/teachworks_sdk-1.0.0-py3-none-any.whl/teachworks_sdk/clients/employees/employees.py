from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import TypeAdapter

from teachworks_sdk.models import (
    CustomFieldUpdateItem,
    CustomFieldUpdateResponse,
    Employee,
    EmployeeEarnings,
    EmployeeLessonTotals,
    EmployeeListParams,
)

if TYPE_CHECKING:
    from teachworks_sdk.session import TeachworksSession

class EmployeesClient:
    """Client for Teachworks employee endpoints."""

    def __init__(self, session: TeachworksSession) -> None:
        """Initialize the employees client.

        :param session: Active TeachworksSession instance.
        :type session: TeachworksSession
        """
        self._session = session

    def retrieve(self, employee_id: int) -> Employee:
        """Retrieve an employee by ID.

        :param employee_id: Employee identifier.
        :type employee_id: int
        :returns: The requested employee.
        :rtype: Employee
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        return self._session._retrieve("/employees", Employee, employee_id)

    def retrieve_earnings(self, employee_id: int) -> EmployeeEarnings:
        """Retrieve earnings for an employee.

        :param employee_id: Employee identifier.
        :type employee_id: int
        :returns: Employee earnings summary.
        :rtype: EmployeeEarnings
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("GET", f"/employees/{employee_id}/earnings")
        return self._session._parse_model(EmployeeEarnings, data)

    def retrieve_lesson_totals(self, employee_id: int) -> EmployeeLessonTotals:
        """Retrieve lesson totals for an employee.

        :param employee_id: Employee identifier.
        :type employee_id: int
        :returns: Employee lesson totals.
        :rtype: EmployeeLessonTotals
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("GET", f"/employees/{employee_id}/lesson_totals")
        return self._session._parse_model(EmployeeLessonTotals, data)

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        query: EmployeeListParams | None = None,
        params: Dict[str, Any] | None = None,
    ) -> List[Employee]:
        """List employees with SDK pagination and filters.

        Pagination is controlled by page and per_page at the SDK level. Use query for resource-specific filters. Use params as an advanced escape hatch; it overrides query on conflicts.

        :param page: SDK-level page number (1-based).
        :type page: int | None
        :param per_page: SDK-level page size.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param query: Preferred typed filter parameters for this resource.
        :type query: EmployeeListParams | None
        :param params: Advanced escape hatch for unsupported query parameters; overrides query on conflicts.
        :type params: dict[str, Any] | None
        :returns: List of employees.
        :rtype: list[Employee]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        merged_params: Dict[str, Any] = {}
        if query is not None:
            merged_params.update(query.to_query_params())
        if params:
            merged_params.update(params)
        return self._session._list(
            "/employees",
            Employee,
            page=page,
            per_page=per_page,
            all_pages=all_pages,
            params=merged_params or None,
        )

    def create(self, payload: Dict[str, Any]) -> Employee:
        """Create a new employee.

        :param payload: Employee payload matching Teachworks API parameters.
        :type payload: dict[str, Any]
        :returns: Created employee.
        :rtype: Employee
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("POST", "/employees", payload=payload)
        return self._session._parse_model(Employee, data)

    def update(self, employee_id: int, payload: Dict[str, Any]) -> Employee:
        """Update an employee.

        :param employee_id: Employee identifier.
        :type employee_id: int
        :param payload: Update payload matching Teachworks API parameters.
        :type payload: dict[str, Any]
        :returns: Updated employee.
        :rtype: Employee
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("PUT", f"/employees/{employee_id}", payload=payload)
        return self._session._handle_update_response(Employee, employee_id, data)

    def set_status(self, employee_id: int, payload: Dict[str, Any]) -> Employee:
        """Set employee status.

        :param employee_id: Employee identifier.
        :type employee_id: int
        :param payload: Status update payload.
        :type payload: dict[str, Any]
        :returns: Updated employee.
        :rtype: Employee
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        data = self._session._request("PUT", f"/employees/{employee_id}/set_status", payload=payload)
        return self._session._parse_model(Employee, data)

    def set_custom_fields(
        self,
        employee_id: int,
        payload: list[CustomFieldUpdateItem],
    ) -> CustomFieldUpdateResponse:
        """Set employee custom field values.

        :param employee_id: Employee identifier.
        :type employee_id: int
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
            f"/employees/{employee_id}/custom_fields",
            payload={"custom_fields": [item.model_dump() for item in items]},
        )
        return self._session._parse_model(CustomFieldUpdateResponse, data)
