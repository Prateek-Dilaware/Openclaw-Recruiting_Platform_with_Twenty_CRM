"""Create the Schema V2 workflow catalogue.

Twenty workflow authoring is currently GraphQL-only and workflow step payloads
vary by Twenty release. This script safely provisions the named workflow records
and their draft versions through the standard Twenty REST record API. It does not
publish or configure status-transition steps; those require a reviewed workflow
manifest compatible with the deployed Twenty version.
"""

from __future__ import annotations

from schema_utils import OperationReport, TwentyClient, main_error_boundary

WORKFLOW_NAMES = (
    "Recruiting V2 - Requisition Approval",
    "Recruiting V2 - Application Stage Transition",
    "Recruiting V2 - Interview Lifecycle",
    "Recruiting V2 - Offer Lifecycle",
)


def existing_workflow_names(client: TwentyClient) -> set[str]:
    try:
        return {workflow.get("name") for workflow in client.list_records("workflows") if workflow.get("name")}
    except Exception as exc:
        raise RuntimeError(
            "Unable to list Twenty workflows. Ensure the API key has workflow permissions."
        ) from exc


def main() -> None:
    report = OperationReport("Schema V2 workflow catalogue provisioning report")
    client = TwentyClient()
    try:
        names = existing_workflow_names(client)
        for name in WORKFLOW_NAMES:
            if name in names:
                report.skipped.append(f"Workflow already exists: {name}")
                continue
            client.create_record("workflows", {"name": name})
            report.created.append(f"Workflow draft: {name}")

        report.warnings.append(
            "Draft workflow records were created only. Configure triggers/actions and activate them "
            "in Twenty after validating the deployed workflow GraphQL schema; no direct stage-patch fallback is permitted."
        )
        report.print()
    finally:
        client.close()


if __name__ == "__main__":
    main_error_boundary(main)
