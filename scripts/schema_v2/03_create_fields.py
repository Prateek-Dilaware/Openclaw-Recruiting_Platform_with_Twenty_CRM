"""Create Schema V2 scalar and select fields idempotently."""

from __future__ import annotations

import json
import sys

import httpx

from schema_utils import FIELD_DEFINITIONS, OperationReport, TwentyClient, get_field_map, main_error_boundary


def main() -> None:
    report = OperationReport("Schema V2 field provisioning report")
    client = TwentyClient()
    try:
        object_map = client.get_object_map()
        missing_objects = [name for name in FIELD_DEFINITIONS if name not in object_map]
        if missing_objects:
            raise RuntimeError(f"Missing required objects: {', '.join(missing_objects)}. Run 02_create_objects.py first.")

        for object_name, definitions in FIELD_DEFINITIONS.items():
            object_metadata = object_map[object_name]
            existing_fields = get_field_map(object_metadata)
            for definition in definitions:
                field_name = definition["name"]
                if field_name in existing_fields:
                    actual_type = existing_fields[field_name].get("type")
                    if actual_type != definition["type"]:
                        report.errors.append(
                            f"{object_name}.{field_name} exists as {actual_type}; expected {definition['type']}"
                        )
                    else:
                        report.skipped.append(f"Field already exists: {object_name}.{field_name}")
                    continue

                payload = {**definition, "objectMetadataId": object_metadata["id"]}
                try:
                    client.create_field(payload)
                except httpx.HTTPStatusError as exc:
                    response = exc.response
                    print(
                        "\n[FIELD CREATION FAILED]\n"
                        f"Object API name: {object_name}\n"
                        f"Field API name: {definition['name']}\n"
                        f"Field label: {definition['label']}\n"
                        f"Field type: {definition['type']}\n"
                        "JSON payload:\n"
                        f"{json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)}\n"
                        f"HTTP status code: {response.status_code}\n"
                        "Twenty response body:\n"
                        f"{response.text}\n",
                        file=sys.stderr,
                    )
                    raise
                report.created.append(f"Field: {object_name}.{field_name}")

        report.print()
        if report.errors:
            raise RuntimeError("Field provisioning found incompatible existing metadata.")
    finally:
        client.close()


if __name__ == "__main__":
    main_error_boundary(main)
