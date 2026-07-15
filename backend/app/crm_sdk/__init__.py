"""CRM SDK — reusable infrastructure foundation.

Phase 1.2 deliverable: a stable transport/config/auth/validation/metadata/router
foundation extracted from the working `TwentyService` REST implementation.

This package contains **no recruiting business logic**. Business objects
(Candidate, Requisition, Application, Interview, Evaluation, Offer, Search,
Workflow) migrate onto this foundation in future phases.

`TwentyService` consumes `CRMClient` internally; all other modules are foundation
scaffolding for upcoming phases.
"""

from __future__ import annotations

from app.crm_sdk.auth import build_headers
from app.crm_sdk.client import CRMClient
from app.crm_sdk.config import CRMConfig
from app.crm_sdk.exceptions import (
    AuthenticationError,
    ConflictError,
    CRMError,
    CRMRequestError,
    NotFoundError,
    RateLimitError,
    RequestError,
    ValidationError,
)
from app.crm_sdk.metadata import MetadataProvider, MetadataRegistry
from app.crm_sdk.models import APIResponse, ErrorResponse, Pagination, RequestContext
from app.crm_sdk.router import CRMRouter

__all__ = [
    "CRMClient",
    "CRMConfig",
    "build_headers",
    "CRMError",
    "AuthenticationError",
    "ValidationError",
    "RequestError",
    "CRMRequestError",
    "RateLimitError",
    "NotFoundError",
    "ConflictError",
    "APIResponse",
    "ErrorResponse",
    "Pagination",
    "RequestContext",
    "MetadataProvider",
    "MetadataRegistry",
    "CRMRouter",
]
