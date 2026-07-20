"""CRM SDK action router skeleton.

Defines the dispatch *structure* only. No business handlers are implemented in
Phase 1.2. Future phases register handlers per namespace (candidate.*,
requisition.*, application.*, ...) following the `object.verb` convention from
TWENTY_SKILL_V2_AUDIT.md.

This router is standalone infrastructure and is NOT used by TwentyService or any
API route yet, so it introduces no behavior change.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Dict, List

from app.crm_sdk.exceptions import ValidationError

# A handler takes a params dict and returns an awaitable result.
Handler = Callable[[Dict[str, object]], Awaitable[object]]

# Reserved action namespaces (no handlers yet). These mirror the V2 audit's
# public action surface. Presence here documents intent; it does not implement.
KNOWN_NAMESPACES: tuple[str, ...] = (
    "candidate",
    "requisition",
    "application",
    "interview",
    "evaluation",
    "offer",
    "workflow",
    "search",
    "metadata",
)


class CRMRouter:
    """Minimal action dispatcher keyed by ``"<namespace>.<verb>"`` strings."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Handler] = {}

    def register(self, action: str, handler: Handler) -> None:
        """Register a handler for an ``"<namespace>.<verb>"`` action."""
        namespace = action.split(".", 1)[0]
        if namespace not in KNOWN_NAMESPACES:
            raise ValidationError(
                f"Unknown action namespace '{namespace}'. "
                f"Expected one of: {', '.join(KNOWN_NAMESPACES)}"
            )
        self._handlers[action] = handler

    def has(self, action: str) -> bool:
        return action in self._handlers

    def actions(self) -> List[str]:
        return sorted(self._handlers)

    async def dispatch(self, action: str, params: Dict[str, object]) -> object:
        """Dispatch an action to its registered handler.

        No handlers are registered in Phase 1.2, so this raises ``ValidationError``
        for every action until future phases populate the router.
        """
        handler = self._handlers.get(action)
        if handler is None:
            raise ValidationError(f"No handler registered for action: {action!r}")
        return await handler(params)
