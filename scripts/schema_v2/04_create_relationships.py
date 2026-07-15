"""Create Schema V2 workflow relationships idempotently."""

from __future__ import annotations

from schema_utils import (
    RELATIONSHIP_DEFINITIONS,
    OperationReport,
    TwentyClient,
    get_field_map,
    main_error_boundary,
    relation_payload,
)


def main() -> None:
    report = OperationReport("Schema V2 relationship provisioning report")
    client = TwentyClient()
    try:
        object_map = client.get_object_map()
        required_objects = {relation["source"] for relation in RELATIONSHIP_DEFINITIONS} | {
            relation["target"] for relation in RELATIONSHIP_DEFINITIONS
        }
        missing = sorted(required_objects - object_map.keys())
        if missing:
            raise RuntimeError(f"Missing required objects: {', '.join(missing)}. Run 02_create_objects.py first.")

        for relation in RELATIONSHIP_DEFINITIONS:
            source = object_map[relation["source"]]
            target = object_map[relation["target"]]
            source_fields = get_field_map(source)
            target_fields = get_field_map(target)
            source_name = relation["field"]
            inverse_name = relation["inverse_field"]
            description = f"{relation['source']}.{source_name} -> {relation['target']}"

            if source_name in source_fields:
                existing = source_fields[source_name]
                if existing.get("type") != "RELATION":
                    report.errors.append(f"{description} conflicts with non-relation field.")
                else:
                    report.skipped.append(f"Relationship already exists: {description}")
                continue
            if inverse_name in target_fields:
                report.errors.append(
                    f"{description} cannot be created because target inverse field "
                    f"{relation['target']}.{inverse_name} already exists."
                )
                continue

            client.create_field(relation_payload(source["id"], target["id"], relation))
            report.created.append(f"Relationship: {description}")

        report.print()
        if report.errors:
            raise RuntimeError("Relationship provisioning found incompatible existing metadata.")
    finally:
        client.close()


if __name__ == "__main__":
    main_error_boundary(main)
