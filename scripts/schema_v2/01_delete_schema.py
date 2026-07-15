"""Idempotently remove only CRM custom objects owned by this project.

Twenty deletes a relation by deleting either endpoint RELATION field. This script
therefore deletes each relation once, removes project custom fields, deactivates
project custom objects, and deletes them. Standard Twenty objects are never
selected because the target set is an explicit project allowlist.
"""

from __future__ import annotations

from schema_utils import PROJECT_OBJECTS, OperationReport, TwentyClient, get_field_map, main_error_boundary


def is_relation(field: dict) -> bool:
    return field.get("type") == "RELATION"


def relation_key(field: dict) -> tuple[str, ...]:
    settings = field.get("settings") or {}
    companion = settings.get("relationFieldMetadataId") or settings.get("relationFieldId")
    return tuple(sorted((field["id"], companion))) if companion else (field["id"],)


def main() -> None:
    report = OperationReport("Schema V2 deletion report")
    client = TwentyClient()
    try:
        object_map = client.get_object_map()
        project_objects = {
            name: object_map[name]
            for name in PROJECT_OBJECTS
            if name in object_map and not object_map[name].get("isSystem", False)
        }
        for name in PROJECT_OBJECTS:
            if name in object_map and object_map[name].get("isSystem", False):
                report.skipped.append(f"Standard/system object preserved: {name}")
        for name, metadata in object_map.items():
            if name not in PROJECT_OBJECTS and not metadata.get("isSystem", False):
                report.skipped.append(f"Non-project custom object preserved: {name}")

        if not project_objects:
            report.skipped.append("No legacy or Schema V2 project objects found.")
            report.print()
            return

        # Step 1: relations. Deleting one endpoint removes its companion endpoint.
        deleted_relation_keys: set[tuple[str, ...]] = set()
        for object_name, obj in project_objects.items():
            for field in obj.get("fields", []):
                if not is_relation(field) or field.get("isSystem", False):
                    continue
                key = relation_key(field)
                if key in deleted_relation_keys:
                    continue
                deleted_relation_keys.add(key)
                detail = f"{object_name}.{field['name']}"
                try:
                    status, _ = client.delete_field(field["id"])
                    if status == 404:
                        report.skipped.append(f"Relationship already absent: {detail}")
                    else:
                        report.deleted.append(f"Relationship: {detail}")
                except Exception as exc:
                    report.errors.append(f"Could not delete relationship {detail}: {exc}")

        # Step 2: non-system fields on objects that this project owns. Twenty
        # rejects any protected standard field; it is recorded as a warning and
        # the object deletion step remains responsible for table cleanup.
        for object_name, obj in project_objects.items():
            for field in obj.get("fields", []):
                if is_relation(field) or field.get("isSystem", False):
                    continue
                try:
                    status, _ = client.delete_field(field["id"])
                    detail = f"{object_name}.{field['name']}"
                    if status == 404:
                        report.skipped.append(f"Field already absent: {detail}")
                    else:
                        report.deleted.append(f"Field: {detail}")
                except Exception as exc:
                    report.warnings.append(
                        f"Field preserved for object-delete cascade: {object_name}.{field['name']} ({exc})"
                    )

        # Step 3: object metadata. Deactivation is required by Twenty before
        # object deletion. Re-fetching is unnecessary because deletion is safe
        # when its fields/relations have already been removed.
        for object_name, obj in project_objects.items():
            object_id = obj["id"]
            try:
                status, _ = client.deactivate_object(object_id)
                if status == 404:
                    report.skipped.append(f"Object already absent during deactivation: {object_name}")
                    continue
                status, _ = client.delete_object(object_id)
                if status == 404:
                    report.skipped.append(f"Object already absent: {object_name}")
                else:
                    report.deleted.append(f"Object: {object_name}")
            except Exception as exc:
                report.errors.append(f"Could not delete object {object_name}: {exc}")

        report.print()
        if report.errors:
            raise RuntimeError("Schema deletion completed with errors.")
    finally:
        client.close()


if __name__ == "__main__":
    main_error_boundary(main)
