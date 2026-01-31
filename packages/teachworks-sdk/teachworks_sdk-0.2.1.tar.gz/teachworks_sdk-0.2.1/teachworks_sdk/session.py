"""Session management and API operations for Teachworks."""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar

import requests
from pydantic import TypeAdapter

from teachworks_sdk.clients import (
    AvailabilitiesClient,
    CostPremiumsClient,
    CreditNoteAllocationsClient,
    CustomersClient,
    EmployeesClient,
    InvoicesClient,
    LessonParticipantsClient,
    LessonsClient,
    LocationsClient,
    OtherCompensationClient,
    OtherEventsClient,
    PaymentAllocationsClient,
    PaymentsClient,
    RepertoiresClient,
    ResultGroupsClient,
    ResultsClient,
    ServicesClient,
    StudentGroupsClient,
    StudentsClient,
    SubjectsClient,
    UnavailabilitiesClient,
    WagePaymentsClient,
    WageTiersClient,
)
from teachworks_sdk.errors import TeachworksAPIError, TeachworksRateLimitError, TeachworksInvalidPathError
from teachworks_sdk.logging_utils import get_logger
from teachworks_sdk.models.base import TeachworksBaseModel, TeachworksErrorResponse

T = TypeVar("T")


class TeachworksSession:
    """Manage Teachworks API requests with rate limiting and retries.

    :param api_key: Teachworks API token.
    :type api_key: str
    :param base_url: Base URL for Teachworks API.
    :type base_url: str
    :param timeout: Default request timeout in seconds.
    :type timeout: float
    :param rate_limit_per_second: Maximum requests per second.
    :type rate_limit_per_second: float
    :param max_retries: Maximum retry attempts for retryable errors.
    :type max_retries: int
    :param backoff_factor: Initial delay for exponential backoff in seconds.
    :type backoff_factor: float
    :param cache_enabled: Enable session-level identity map caching for models.
    :type cache_enabled: bool
    :param logger: Custom logger instance. If None, uses default SDK logger.
    :type logger: logging.Logger | None
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.teachworks.com/v1",
        timeout: float = 30.0,
        rate_limit_per_second: float = 4.0,
        max_retries: int = 5,
        backoff_factor: float = 0.5,
        cache_enabled: bool = True,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the Teachworks session.

        :param api_key: Teachworks API token.
        :type api_key: str
        :param base_url: Base URL for Teachworks API.
        :type base_url: str
        :param timeout: Default request timeout in seconds.
        :type timeout: float
        :param rate_limit_per_second: Maximum requests per second.
        :type rate_limit_per_second: float
        :param max_retries: Maximum retry attempts for retryable errors.
        :type max_retries: int
        :param backoff_factor: Initial delay for exponential backoff in seconds.
        :type backoff_factor: float
        :param cache_enabled: Enable session-level identity map caching for models.
        :type cache_enabled: bool
        :param logger: Custom logger instance. If None, uses default SDK logger.
        :type logger: logging.Logger | None
        """
        self.logger = logger or get_logger("session")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit_per_second = rate_limit_per_second
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.cache_enabled = cache_enabled
        self._last_request_time: float | None = None
        self._cache: Dict[tuple[type, int], Any] = {}
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Token token={api_key}",
                "Content-Type": "application/json",
            }
        )

        self.locations = LocationsClient(self)
        self.services = ServicesClient(self)
        self.wage_tiers = WageTiersClient(self)
        self.cost_premiums = CostPremiumsClient(self)
        self.employees = EmployeesClient(self)
        self.customers = CustomersClient(self)
        self.students = StudentsClient(self)
        self.subjects = SubjectsClient(self)
        self.student_groups = StudentGroupsClient(self)
        self.lessons = LessonsClient(self)
        self.lesson_participants = LessonParticipantsClient(self)
        self.other_events = OtherEventsClient(self)
        self.availabilities = AvailabilitiesClient(self)
        self.unavailabilities = UnavailabilitiesClient(self)
        self.invoices = InvoicesClient(self)
        self.payments = PaymentsClient(self)
        self.payment_allocations = PaymentAllocationsClient(self)
        self.credit_note_allocations = CreditNoteAllocationsClient(self)
        self.other_compensation = OtherCompensationClient(self)
        self.wage_payments = WagePaymentsClient(self)
        self.result_groups = ResultGroupsClient(self)
        self.results = ResultsClient(self)
        self.repertoires = RepertoiresClient(self)

        self.logger.info(
            "Teachworks session initialized (base_url=%s, timeout=%.1fs, rate_limit=%.1f/s, max_retries=%d, cache_enabled=%s)",
            self.base_url,
            self.timeout,
            self.rate_limit_per_second,
            self.max_retries,
            self.cache_enabled,
        )

    def clear_cache(self) -> None:
        """Clear cached model instances for this session."""
        cache_size = len(self._cache)
        self._cache.clear()
        self.logger.debug("Cache cleared (removed %d entries)", cache_size)

    def _cache_get(self, model: Type[T], model_id: int) -> T | None:
        """Return a cached model instance if available."""
        if not self.cache_enabled:
            return None
        cached = self._cache.get((model, model_id))
        if cached is None:
            self.logger.debug("Cache miss: %s(id=%d)", model.__name__, model_id)
            return None
        self.logger.debug("Cache hit: %s(id=%d)", model.__name__, model_id)
        return cached

    def _cache_set(self, model: Type[T], model_id: int, instance: T) -> None:
        """Store a model instance in the session cache."""
        if not self.cache_enabled:
            return
        self._cache[(model, model_id)] = instance
        self.logger.debug("Cached: %s(id=%d)", model.__name__, model_id)

    def _cache_invalidate(self, model: Type[T], model_id: int) -> None:
        """Remove a model instance from the session cache."""
        if not self.cache_enabled:
            return
        removed = self._cache.pop((model, model_id), None)
        if removed is not None:
            self.logger.debug("Cache invalidated: %s(id=%d)", model.__name__, model_id)

    def invalidate(self, model: Type[T], model_id: int) -> None:
        """Public cache invalidation helper for a specific model/id."""
        self._cache_invalidate(model, model_id)

    def __enter__(self) -> "TeachworksSession":
        """Enter the runtime context for the session.

        :returns: The active TeachworksSession instance.
        :rtype: TeachworksSession
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Exit the runtime context and close resources.

        :param exc_type: Exception type if raised.
        :type exc_type: type | None
        :param exc: Exception instance if raised.
        :type exc: BaseException | None
        :param tb: Traceback if raised.
        :type tb: TracebackType | None
        """
        self.close()

    def close(self) -> None:
        """Close the underlying requests session.

        :returns: None
        :rtype: None
        """
        self._session.close()
        self.logger.info("Teachworks session closed")

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests.

        :returns: None
        :rtype: None
        """
        if self.rate_limit_per_second <= 0:
            return
        min_interval = 1.0 / self.rate_limit_per_second
        now = time.monotonic()
        if self._last_request_time is None:
            self._last_request_time = now
            return
        elapsed = now - self._last_request_time
        if elapsed < min_interval:
            delay = min_interval - elapsed
            self.logger.debug("Rate limiting: sleeping %.3fs", delay)
            time.sleep(delay)
        self._last_request_time = time.monotonic()

    def _should_retry(self, response: requests.Response) -> bool:
        """Determine whether a response qualifies for retry.

        :param response: HTTP response to evaluate.
        :type response: requests.Response
        :returns: True if retry should be attempted.
        :rtype: bool
        """
        should_retry = False
        if response.status_code in {429, 502, 503, 504}:
            should_retry = True
        elif response.status_code == 403:
            try:
                data = response.json()
            except json.JSONDecodeError:
                return False
            # Handle both dict and list responses
            if not isinstance(data, dict):
                return False
            message = str(data.get("message", "")).lower()
            should_retry = "rate" in message or "limit" in message

        if should_retry:
            self.logger.debug("Retryable error detected: status_code=%d", response.status_code)
        return should_retry

    def _handle_error(self, response: requests.Response) -> None:
        """Raise a Teachworks exception for error responses.

        :param response: HTTP response to interpret.
        :type response: requests.Response
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = {"message": response.text}

        # Handle list responses (e.g., ['Rate Limit Exceeded'])
        if isinstance(payload, list):
            message = ", ".join(str(item) for item in payload) if payload else response.text
            payload = {"message": message}

        error = TeachworksErrorResponse.model_validate(payload)
        message = error.message or f"Teachworks API error ({response.status_code})."
        code = error.code
        data = error.data

        self.logger.error(
            "API error: status_code=%d, message=%s, code=%s, url=%s",
            response.status_code,
            message,
            code,
            response.url,
        )

        if response.status_code in {429, 403}:
            raise TeachworksRateLimitError(response.status_code, message, code=code, data=data)
        if response.status_code == 404:
            raise TeachworksInvalidPathError(response.status_code, message, code=code, data=data, url=response.url)
        raise TeachworksAPIError(response.status_code, message, code=code, data=data)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        payload: Dict[str, Any] | None = None,
    ) -> Any:
        """Perform an HTTP request with retry and backoff logic.

        :param method: HTTP method (GET, POST, PUT, etc.).
        :type method: str
        :param path: Request path relative to the base URL.
        :type path: str
        :param params: Query string parameters.
        :type params: dict[str, Any] | None
        :param payload: JSON payload for the request.
        :type payload: dict[str, Any] | None
        :returns: Parsed JSON response payload.
        :rtype: Any
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        url = f"{self.base_url}{path}"
        attempt = 0

        # Log request details at DEBUG level
        self.logger.debug(
            "API request: method=%s, path=%s, params=%s, has_payload=%s",
            method,
            path,
            params,
            payload is not None,
        )

        while True:
            self._rate_limit()
            response = self._session.request(
                method,
                url,
                params=params,
                json=payload,
                timeout=self.timeout,
            )

            # Log response status
            if response.ok:
                self.logger.debug(
                    "API response: method=%s, path=%s, status_code=%d",
                    method,
                    path,
                    response.status_code,
                )
                if response.text:
                    return response.json()
                return None

            if self._should_retry(response) and attempt < self.max_retries:
                delay = self.backoff_factor * (2**attempt)
                delay += random.uniform(0, 0.1)
                attempt += 1
                self.logger.warning(
                    "Retrying request: method=%s, path=%s, attempt=%d/%d, delay=%.2fs, status_code=%d",
                    method,
                    path,
                    attempt,
                    self.max_retries,
                    delay,
                    response.status_code,
                )
                time.sleep(delay)
                continue

            self._handle_error(response)

    def _parse_model(self, model: Type[T], payload: Any) -> T:
        """Parse a payload into a Pydantic model.

        :param model: Pydantic model class.
        :type model: type[T]
        :param payload: Raw response payload.
        :type payload: Any
        :returns: Parsed model instance.
        :rtype: T
        """
        self.logger.debug("Parsing model: %s", model.__name__)
        parsed = model.model_validate(payload)
        model_id = getattr(parsed, "id", None)
        if isinstance(model_id, int):
            self._cache_set(model, model_id, parsed)
        self._cache_models(parsed)
        return parsed

    def _try_parse_model(self, model: Type[T], payload: Any) -> T | None:
        """Attempt to parse a payload into a model without raising."""
        try:
            return model.model_validate(payload)
        except Exception:
            return None

    def _is_full_resource_payload(self, model: Type[T], payload: Any, model_id: int) -> bool:
        """Heuristically determine if payload looks like a full resource."""
        if not isinstance(payload, dict):
            return False
        if payload.get("id") != model_id:
            return False
        keys = set(payload.keys())
        if keys in ({"id"}, {"success"}):
            return False
        model_fields = set(model.model_fields.keys())
        extra_fields = {key for key in keys if key != "id"}
        return bool(extra_fields & model_fields)

    def _is_full_resource_instance(self, instance: TeachworksBaseModel) -> bool:
        """Determine if a model instance looks like a full resource."""
        fields_set = instance.model_fields_set
        if not fields_set:
            return False
        return fields_set != {"id"}

    def _cache_models(self, obj: Any) -> None:
        """Cache nested Teachworks models within parsed payloads."""
        if not self.cache_enabled or obj is None:
            return
        if isinstance(obj, TeachworksBaseModel):
            model_id = getattr(obj, "id", None)
            if (
                getattr(obj, "__cacheable__", True)
                and isinstance(model_id, int)
                and self._is_full_resource_instance(obj)
            ):
                self._cache_set(type(obj), model_id, obj)
            for field_name in type(obj).model_fields:
                self._cache_models(getattr(obj, field_name))
            return
        if isinstance(obj, dict):
            for value in obj.values():
                self._cache_models(value)
            return
        if isinstance(obj, (list, tuple)):
            for item in obj:
                self._cache_models(item)
            return

    def _handle_update_response(self, model: Type[T], model_id: int, payload: Any) -> T | None:
        """Parse update responses and keep cache consistent."""
        parsed = self._try_parse_model(model, payload)
        if parsed is not None and self._is_full_resource_payload(model, payload, model_id):
            self._cache_set(model, model_id, parsed)
            self._cache_models(parsed)
            return parsed
        self._cache_invalidate(model, model_id)
        return parsed

    def _retrieve(self, path: str, model: Type[T], model_id: int) -> T:
        """Retrieve a model by ID with optional session-level caching.

        :param path: Resource path.
        :type path: str
        :param model: Pydantic model class.
        :type model: type[T]
        :param model_id: Resource identifier.
        :type model_id: int
        :returns: Parsed model instance.
        :rtype: T
        """
        self.logger.debug("Retrieving: %s(id=%d) from path=%s", model.__name__, model_id, path)
        cached = self._cache_get(model, model_id)
        if cached is not None:
            return cached
        data = self._request("GET", f"{path}/{model_id}")
        return self._parse_model(model, data)

    def _parse_list(self, model: Type[T], payload: Any) -> List[T]:
        """Parse a list payload into Pydantic models.

        :param model: Pydantic model class.
        :type model: type[T]
        :param payload: Raw response payload.
        :type payload: Any
        :returns: List of parsed model instances.
        :rtype: list[T]
        """
        adapter = TypeAdapter(List[model])
        parsed = adapter.validate_python(payload)
        self.logger.debug("Parsed list of %d %s instances", len(parsed), model.__name__)
        for item in parsed:
            self._cache_models(item)
        return parsed

    def _list(
        self,
        path: str,
        model: Type[T],
        *,
        page: int | None = None,
        per_page: int | None = None,
        all_pages: bool = False,
        params: Dict[str, Any] | None = None,
    ) -> List[T]:
        """Fetch a list of resources with pagination options.

        :param path: Resource path.
        :type path: str
        :param model: Pydantic model class.
        :type model: type[T]
        :param page: Page number (1-based).
        :type page: int | None
        :param per_page: Number of results per page.
        :type per_page: int | None
        :param all_pages: If True, fetch all pages.
        :type all_pages: bool
        :param params: Additional query parameters.
        :type params: dict[str, Any] | None
        :returns: List of parsed model instances.
        :rtype: list[T]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        self.logger.debug(
            "Listing: %s from path=%s (page=%s, per_page=%s, all_pages=%s, params=%s)",
            model.__name__,
            path,
            page,
            per_page,
            all_pages,
            params,
        )

        request_params = dict(params or {})
        if per_page is not None:
            request_params["per_page"] = per_page
        if all_pages:
            results = list(self._paginate(path, model, request_params=request_params))
            self.logger.info("Listed %d %s (all pages) from path=%s", len(results), model.__name__, path)
            return results
        if page is not None:
            request_params["page"] = page
        payload = self._request("GET", path, params=request_params)
        return self._parse_list(model, payload)

    def _paginate(
        self,
        path: str,
        model: Type[T],
        *,
        request_params: Dict[str, Any] | None = None,
    ) -> Iterable[T]:
        """Yield items across paginated responses.

        :param path: Resource path.
        :type path: str
        :param model: Pydantic model class.
        :type model: type[T]
        :param request_params: Base query parameters for each request.
        :type request_params: dict[str, Any] | None
        :returns: Iterator over parsed model instances.
        :rtype: Iterable[T]
        :raises TeachworksAPIError: For non-retryable API errors.
        :raises TeachworksRateLimitError: When rate limits persist after retries.
        """
        self.logger.debug("Starting pagination: %s from path=%s", model.__name__, path)
        page = 1
        total_items = 0
        params = dict(request_params or {})
        while True:
            params["page"] = page
            self.logger.debug("Fetching page %d for %s from path=%s", page, model.__name__, path)
            payload = self._request("GET", path, params=params)
            items = self._parse_list(model, payload)
            if not items:
                self.logger.debug(
                    "Pagination complete: %s from path=%s (total_items=%d, total_pages=%d)",
                    model.__name__,
                    path,
                    total_items,
                    page - 1,
                )
                break
            total_items += len(items)
            for item in items:
                yield item
            page += 1
