"""Verify Schema V2 metadata, required select values, and seeded demo records."""

from __future__ import annotations

from schema_utils import (
    FIELD_DEFINITIONS,
    RELATIONSHIP_DEFINITIONS,
    REQUIRED_SELECT_VALUES,
    V2_OBJECTS,
    OperationReport,
    TwentyClient,
    get_field_map,
    main_error_boundary,
)


def option_values(field: dict) -> set[str]:
    options = field.get("options") or (field.get("settings") or {}).get("options") or []
    return {option.get("value") for option in options if option.get("value")}


def relation_target_name(field: dict, object_map: dict[str, dict]) -> str | None:
    settings = field.get("settings") or {}
    target_id = settings.get("relationTargetObjectMetadataId") or settings.get("targetObjectMetadataId")
    if not target_id:
        return None
    return next((name for name, obj in object_map.items() if obj.get("id") == target_id), None)


def relation_targets_expected_object(field: dict, target: dict) -> bool:
    """Check target metadata when the deployed Twenty response exposes it."""
    settings = field.get("settings") or {}
    target_id = settings.get("relationTargetObjectMetadataId") or settings.get("targetObjectMetadataId")
    return not target_id or target_id == target.get("id")


def main() -> None:
    report = OperationReport("Schema V2 validation report")
    client = TwentyClient()
    try:
        object_map = client.get_object_map()
        for object_name in V2_OBJECTS:
            if object_name in object_map:
                report.validated.append(f"Object exists: {object_name}")
            else:
                report.errors.append(f"Missing object: {object_name}")

        for object_name, definitions in FIELD_DEFINITIONS.items():
            obj = object_map.get(object_name)
            if not obj:
                continue
            existing = get_field_map(obj)
            for definition in definitions:
                field = existing.get(definition["name"])
                if not field:
                    report.errors.append(f"Missing field: {object_name}.{definition['name']}")
                elif field.get("type") != definition["type"]:
                    report.errors.append(
                        f"Wrong field type: {object_name}.{definition['name']} is {field.get('type')}, expected {definition['type']}"
                    )
                else:
                    report.validated.append(f"Field exists: {object_name}.{definition['name']}")

        for (object_name, field_name), required_values in REQUIRED_SELECT_VALUES.items():
            obj = object_map.get(object_name)
            field = get_field_map(obj).get(field_name) if obj else None
            actual_values = option_values(field or {})
            missing = required_values - actual_values
            if missing:
                report.errors.append(f"Missing enum values on {object_name}.{field_name}: {', '.join(sorted(missing))}")
            else:
                report.validated.append(f"Required enum values exist: {object_name}.{field_name}")

        for relation in RELATIONSHIP_DEFINITIONS:
            source = object_map.get(relation["source"])
            target = object_map.get(relation["target"])
            if not source or not target:
                continue
            source_field = get_field_map(source).get(relation["field"])
            inverse_field = get_field_map(target).get(relation["inverse_field"])
            description = f"{relation['source']}.{relation['field']} -> {relation['target']}"
            if not source_field or source_field.get("type") != "RELATION":
                report.errors.append(f"Missing relation: {description}")
                continue
            if not inverse_field or inverse_field.get("type") != "RELATION":
                report.errors.append(f"Missing inverse relation: {relation['target']}.{relation['inverse_field']}")
                continue
            resolved_target = relation_target_name(source_field, object_map)
            if not relation_targets_expected_object(source_field, target):
                report.errors.append(
                    f"Wrong relation target: {description} resolves to {resolved_target or 'a different metadata id'}"
                )
                continue
            report.validated.append(f"Relationship exists: {description}")

        expected_demo_names = {
            "candidates": {"Ada Lovelace", "Grace Hopper", "Margaret Hamilton"},
            "requisitions": {"REQ-2026-001 Senior Backend Engineer", "REQ-2026-002 Frontend Engineer"},
            "applications": {"Ada Lovelace — Senior Backend Engineer", "Grace Hopper — Frontend Engineer", "Margaret Hamilton — Senior Backend Engineer"},
            "interviews": {"Ada Lovelace — Technical Interview", "Grace Hopper — Technical Interview"},
            "evaluations": {"Ada Lovelace — AI Technical Evaluation", "Ada Lovelace — Hiring Manager Evaluation"},
            "offers": {"Ada Lovelace — Senior Backend Engineer Offer"},
        }
        for plural, required_names in expected_demo_names.items():
            records = client.list_records(plural)
            actual_names = {record.get("name") for record in records}
            missing = required_names - actual_names
            if missing:
                report.errors.append(f"Missing demo {plural}: {', '.join(sorted(missing))}")
            else:
                report.validated.append(f"Demo data exists: {plural}")

        # Confirm the linked demo path with actual relation identifiers.
        applications = {record.get("name"): record for record in client.list_records("applications")}
        interviews = {record.get("name"): record for record in client.list_records("interviews")}
        evaluations = {record.get("name"): record for record in client.list_records("evaluations")}
        offers = {record.get("name"): record for record in client.list_records("offers")}
        ada_application = applications.get("Ada Lovelace — Senior Backend Engineer", {})
        ada_interview = interviews.get("Ada Lovelace — Technical Interview", {})
        ada_evaluation = evaluations.get("Ada Lovelace — AI Technical Evaluation", {})
        ada_offer = offers.get("Ada Lovelace — Senior Backend Engineer Offer", {})
        links = (
            ada_application.get("candidateId") and ada_application.get("requisitionId") and
            ada_interview.get("applicationId") == ada_application.get("id") and
            ada_evaluation.get("interviewId") == ada_interview.get("id") and
            ada_offer.get("applicationId") == ada_application.get("id")
        )
        if links:
            report.validated.append("Demo relationship chain is linked correctly.")
        else:
            report.errors.append("Demo relationship chain is incomplete or returned with unexpected relation field names.")

        report.print()
        if report.errors:
            raise RuntimeError("Schema V2 verification failed.")
    finally:
        client.close()


if __name__ == "__main__":
    main_error_boundary(main)
