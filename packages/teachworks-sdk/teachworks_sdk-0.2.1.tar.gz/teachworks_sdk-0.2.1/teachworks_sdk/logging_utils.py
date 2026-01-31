"""
Centralized logging utilities for the Teachworks SDK.

This module provides a lightweight wrapper around Python's built-in logging
module for consistent logging across the SDK.

The SDK follows Python logging best practices:
- Uses hierarchical logger naming under the 'teachworks' namespace
- No handlers are added by default (logs propagate to root logger)
- Never calls logging.basicConfig() to avoid interfering with host apps
- Allows both propagation-based and explicit handler patterns

Usage Patterns
--------------

Pattern 1: Propagation (Recommended for most users)
    Let SDK logs flow through your application's logging configuration:

        >>> import logging
        >>> logging.basicConfig(
        ...     level=logging.INFO,
        ...     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ... )
        >>>
        >>> from teachworks_sdk import TeachworksSession
        >>> session = TeachworksSession(api_key="your-key")
        >>> # SDK logs will appear using your basicConfig settings

    Enable DEBUG logging for SDK only:

        >>> import logging
        >>> logging.basicConfig(level=logging.WARNING)  # App logs at WARNING
        >>> logging.getLogger("teachworks").setLevel(logging.DEBUG)  # SDK logs at DEBUG

Pattern 2: SDK-specific handlers (For isolated SDK logging)
    Configure SDK to log to a separate file or with different formatting:

        >>> from teachworks_sdk import configure_logging
        >>> import logging
        >>>
        >>> # SDK logs go to teachworks.log, app logs go elsewhere
        >>> from logging.handlers import RotatingFileHandler
        >>> handler = RotatingFileHandler("teachworks.log", maxBytes=1e6, backupCount=3)
        >>> configure_logging(handler=handler, level=logging.DEBUG)

    Configure SDK with console output and custom format:

        >>> configure_logging(
        ...     level=logging.DEBUG,
        ...     fmt='[SDK] %(levelname)s - %(message)s'
        ... )

Pattern 3: Custom logger injection
    Inject your own logger for complete control:

        >>> import logging
        >>> my_logger = logging.getLogger("myapp.integrations.teachworks")
        >>> my_logger.addHandler(logging.StreamHandler())
        >>> my_logger.setLevel(logging.DEBUG)
        >>>
        >>> from teachworks_sdk import TeachworksSession
        >>> session = TeachworksSession(api_key="your-key", logger=my_logger)

Logger Hierarchy
----------------
The SDK uses these logger names:
- teachworks.session - Session-level operations (requests, cache, retries)
- teachworks.clients.lessons - Lesson client operations
- teachworks.clients.students - Student client operations
- teachworks.models.resolvers - Relationship resolution

You can configure them individually:
    >>> import logging
    >>> logging.getLogger("teachworks.session").setLevel(logging.DEBUG)
    >>> logging.getLogger("teachworks.clients").setLevel(logging.INFO)
"""

import logging
from typing import Optional

# Root logger namespace for the SDK
ROOT_LOGGER_NAME = "teachworks"

# Default logging configuration
DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DEFAULT_LEVEL = logging.INFO


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for the Teachworks SDK.

    Creates or retrieves a logger in the 'teachworks' namespace hierarchy.
    If no name is provided, returns the root 'teachworks' logger.

    By default, loggers propagate to the root logger, allowing the host
    application to control all logging configuration. No handlers are added
    automatically - call configure_logging() if you want SDK-specific handlers.

    :param name: Optional module or component name. Will be appended to the
                 'teachworks' namespace (e.g., 'session' becomes 'teachworks.session').
                 If None, returns the root 'teachworks' logger.
    :type name: str | None
    :returns: A logger instance (without handlers by default).
    :rtype: logging.Logger

    Example:
        Get a logger that propagates to host app's configuration::

            >>> logger = get_logger("session")
            >>> logger.info("Session initialized")
            # Logs will appear if host app configures logging

        Get the root SDK logger::

            >>> root_logger = get_logger()
            >>> root_logger.info("SDK operation")
    """
    if name:
        logger_name = f"{ROOT_LOGGER_NAME}.{name}"
    else:
        logger_name = ROOT_LOGGER_NAME

    return logging.getLogger(logger_name)


def configure_logging(
    level: Optional[int] = None,
    handler: Optional[logging.Handler] = None,
    fmt: Optional[str] = None,
    logger_name: Optional[str] = None,
    propagate: Optional[bool] = None,
) -> logging.Logger:
    """Configure logging for the Teachworks SDK with explicit handlers.

    Call this function ONLY if you want SDK-specific logging handlers that are
    independent from your host application's logging configuration. If you want
    SDK logs to flow through your application's existing logging setup, configure
    the root logger instead and let propagation work naturally.

    This function adds handlers to the specified logger, which is useful when you
    want isolated SDK logging (e.g., SDK logs to a separate file, or SDK-specific
    formatting).

    :param level: Logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING).
                  Defaults to logging.INFO if not specified.
    :type level: int | None
    :param handler: Custom logging handler (e.g., FileHandler, RotatingFileHandler).
                    If None, uses StreamHandler (console output).
    :type handler: logging.Handler | None
    :param fmt: Custom log message format string. Defaults to
                "%(asctime)s %(levelname)s %(name)s: %(message)s".
    :type fmt: str | None
    :param logger_name: Specific logger to configure. If None, configures the root
                        'teachworks' logger (affects all SDK loggers).
    :type logger_name: str | None
    :param propagate: Whether logs should propagate to parent loggers. If not specified,
                      propagation is disabled when adding handlers (to avoid duplicate logs).
                      Set to True explicitly if you want both SDK-specific handlers AND
                      propagation to parent loggers.
    :type propagate: bool | None
    :returns: The configured logger instance.
    :rtype: logging.Logger

    Example:
        Configure SDK-specific logging to DEBUG level with console output::

            >>> import logging
            >>> from teachworks_sdk import configure_logging
            >>> configure_logging(level=logging.DEBUG)

        Configure SDK logs to a separate file::

            >>> from logging.handlers import RotatingFileHandler
            >>> handler = RotatingFileHandler("teachworks.log", maxBytes=1e6, backupCount=3)
            >>> configure_logging(handler=handler, level=logging.DEBUG)

        Configure specific module logger::

            >>> configure_logging(logger_name="session", level=logging.DEBUG)

        Alternative: Let SDK logs flow through your app's logging configuration::

            >>> import logging
            >>> logging.basicConfig(level=logging.DEBUG, format='%(message)s')
            >>> # Don't call configure_logging() - SDK logs will propagate naturally
    """
    if logger_name:
        target_logger_name = (
            f"{ROOT_LOGGER_NAME}.{logger_name}"
            if not logger_name.startswith(ROOT_LOGGER_NAME)
            else logger_name
        )
    else:
        target_logger_name = ROOT_LOGGER_NAME

    logger = logging.getLogger(target_logger_name)

    # Clear existing handlers if we're reconfiguring
    if logger.handlers:
        logger.handlers.clear()

    # Set up handler
    if handler is None:
        handler = logging.StreamHandler()

    # Set up formatter
    format_string = fmt if fmt is not None else DEFAULT_FORMAT
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    # Configure logger
    logger.addHandler(handler)

    if level is not None:
        logger.setLevel(level)
    elif not logger.level:
        logger.setLevel(DEFAULT_LEVEL)

    # Set propagation
    # When adding SDK-specific handlers, disable propagation by default to avoid
    # duplicate log messages (one from SDK handler, one from root handler).
    # Users can explicitly set propagate=True if they want both.
    if propagate is not None:
        logger.propagate = propagate
    else:
        # Disable propagation when we're adding handlers to avoid duplicates
        logger.propagate = False

    return logger
