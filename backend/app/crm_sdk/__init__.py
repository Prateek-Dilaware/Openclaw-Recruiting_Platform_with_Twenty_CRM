"""CRM SDK — reusable infrastructure foundation + business entity modules.

Foundation (Phase 1.2): a stable transport/config/auth/validation/metadata/router
layer extracted from the working `TwentyService` REST implementation.

Business entity modules (Milestone 2, in progress) encapsulate one CRM entity
each and delegate transport to the shared `CRMClient`:

    Foundation : client, config, auth, exceptions, models, validators,
                 metadata, utility, router
    Business   : requisition ✅, candidate ✅, application ⏳, interview ⏳,
                 evaluation ⏳, offer ⏳, search ⏳, workflow ⏳

See ``MODULE_INDEX.md`` in this package for the authoritative map, per-module
status, and the required module pattern.

`TwentyService` consumes these modules internally as a thin delegation layer.
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
from app.crm_sdk.application import ApplicationModule
from app.crm_sdk.candidate import CandidateModule
from app.crm_sdk.evaluation import EvaluationModule
from app.crm_sdk.interview import InterviewModule
from app.crm_sdk.models import APIResponse, ErrorResponse, Pagination, RequestContext
from app.crm_sdk.offer import OfferModule
from app.crm_sdk.requisition import RequisitionModule
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
    "RequisitionModule",
    "CandidateModule",
    "ApplicationModule",
    "InterviewModule",
    "EvaluationModule",
    "OfferModule",
]
