# Copyright (c) Metis. All rights reserved.

"""Insight OTLP exporter for MantisDK tracing.

This module provides an OTLP/HTTP exporter configured for Mantis Insight,
with support for environment variable auto-detection and Basic Auth headers.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Optional

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)

# Environment variable names (INSIGHT_* prefix)
ENV_INSIGHT_HOST = "INSIGHT_HOST"
ENV_INSIGHT_PUBLIC_KEY = "INSIGHT_PUBLIC_KEY"
ENV_INSIGHT_SECRET_KEY = "INSIGHT_SECRET_KEY"
ENV_INSIGHT_OTLP_ENDPOINT = "INSIGHT_OTLP_ENDPOINT"

# Default OTLP endpoint path
DEFAULT_OTLP_PATH = "/api/public/otel/v1/traces"


class InsightOTLPExporter(OTLPSpanExporter):
    """OTLP exporter configured for Mantis Insight.

    This exporter automatically handles Basic Auth header construction
    from public/secret key pairs.

    Example::

        from mantisdk.tracing_claude.exporters import InsightOTLPExporter

        exporter = InsightOTLPExporter(
            host="https://insight.withmetis.ai",
            public_key="pk-lf-...",
            secret_key="sk-lf-...",
        )
    """

    def __init__(
        self,
        host: str,
        public_key: str,
        secret_key: str,
        *,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Insight OTLP exporter.

        Args:
            host: The Insight server URL (e.g., "https://insight.withmetis.ai").
            public_key: The public key for authentication (pk-lf-...).
            secret_key: The secret key for authentication (sk-lf-...).
            endpoint: Optional full OTLP endpoint URL. If not provided,
                derived from host + DEFAULT_OTLP_PATH.
            **kwargs: Additional arguments passed to OTLPSpanExporter.
        """
        # Derive endpoint from host if not explicitly provided
        if endpoint is None:
            # Remove trailing slash if present
            host = host.rstrip("/")
            endpoint = f"{host}{DEFAULT_OTLP_PATH}"

        # Construct Basic Auth header
        credentials = f"{public_key}:{secret_key}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        auth_header = f"Basic {encoded}"

        # Merge auth header with any user-provided headers
        headers = kwargs.pop("headers", {}) or {}
        headers["Authorization"] = auth_header

        super().__init__(endpoint=endpoint, headers=headers, **kwargs)

        self._insight_host = host
        self._insight_public_key = public_key
        # Don't store secret key in instance for security

        logger.debug(
            "InsightOTLPExporter initialized: endpoint=%s, public_key=%s",
            endpoint,
            public_key[:20] + "..." if len(public_key) > 20 else public_key,
        )

    def __repr__(self) -> str:
        return (
            f"InsightOTLPExporter("
            f"host={self._insight_host!r}, "
            f"public_key={self._insight_public_key[:10]}...)"
        )


def insight(
    *,
    host: Optional[str] = None,
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    **kwargs,
) -> InsightOTLPExporter:
    """Factory function to create an Insight OTLP exporter.

    This function supports both explicit configuration and environment variable
    auto-detection. If any required parameter is not provided, it will be read
    from the corresponding environment variable.

    Environment variables:
        - INSIGHT_HOST: The Insight server URL
        - INSIGHT_PUBLIC_KEY: The public key for authentication
        - INSIGHT_SECRET_KEY: The secret key for authentication
        - INSIGHT_OTLP_ENDPOINT: Optional override for the OTLP endpoint

    Args:
        host: The Insight server URL. Falls back to INSIGHT_HOST env var.
        public_key: The public key. Falls back to INSIGHT_PUBLIC_KEY env var.
        secret_key: The secret key. Falls back to INSIGHT_SECRET_KEY env var.
        endpoint: Optional full OTLP endpoint URL. Falls back to INSIGHT_OTLP_ENDPOINT.
        **kwargs: Additional arguments passed to InsightOTLPExporter.

    Returns:
        Configured InsightOTLPExporter instance.

    Raises:
        ValueError: If required credentials are not provided and not found in env vars.

    Example::

        import mantisdk.tracing_claude as tracing

        # Using environment variables
        tracing.init(exporters=[tracing.insight_exporter()])

        # Explicit configuration
        tracing.init(exporters=[
            tracing.insight_exporter(
                host="https://insight.withmetis.ai",
                public_key="pk-lf-...",
                secret_key="sk-lf-...",
            )
        ])
    """
    # Read from env vars if not provided
    host = host or os.environ.get(ENV_INSIGHT_HOST)
    public_key = public_key or os.environ.get(ENV_INSIGHT_PUBLIC_KEY)
    secret_key = secret_key or os.environ.get(ENV_INSIGHT_SECRET_KEY)
    endpoint = endpoint or os.environ.get(ENV_INSIGHT_OTLP_ENDPOINT)

    # Validate required parameters
    missing = []
    if not host:
        missing.append(f"{ENV_INSIGHT_HOST} (or host parameter)")
    if not public_key:
        missing.append(f"{ENV_INSIGHT_PUBLIC_KEY} (or public_key parameter)")
    if not secret_key:
        missing.append(f"{ENV_INSIGHT_SECRET_KEY} (or secret_key parameter)")

    if missing:
        raise ValueError(
            f"Missing required Insight configuration: {', '.join(missing)}. "
            "Provide these values via function arguments or environment variables."
        )

    return InsightOTLPExporter(
        host=host,
        public_key=public_key,
        secret_key=secret_key,
        endpoint=endpoint,
        **kwargs,
    )


def detect_insight_config() -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Detect Insight configuration from environment variables.

    Returns:
        Tuple of (host, public_key, secret_key, endpoint) where any value may be None
        if the corresponding environment variable is not set.
    """
    return (
        os.environ.get(ENV_INSIGHT_HOST),
        os.environ.get(ENV_INSIGHT_PUBLIC_KEY),
        os.environ.get(ENV_INSIGHT_SECRET_KEY),
        os.environ.get(ENV_INSIGHT_OTLP_ENDPOINT),
    )


def is_insight_configured() -> bool:
    """Check if Insight is configured via environment variables.

    Returns:
        True if all required environment variables are set.
    """
    host, public_key, secret_key, _ = detect_insight_config()
    return all([host, public_key, secret_key])
