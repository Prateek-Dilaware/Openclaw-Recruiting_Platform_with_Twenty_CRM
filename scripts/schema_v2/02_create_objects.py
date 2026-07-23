"""Create the six canonical Schema V2 custom objects idempotently."""

from __future__ import annotations

from schema_utils import OBJECT_DEFINITIONS, OperationReport, TwentyClient, main_error_boundary


def main() -> None:
    report = OperationReport("Schema V2 object provisioning report")
    client = TwentyClient()
    try:
        object_map = client.get_object_map()
        for definition in OBJECT_DEFINITIONS:
            name = definition["nameSingular"]
            if name in object_map:
                report.skipped.append(f"Object already exists: {name} ({object_map[name]['id']})")
                continue
            client.create_object(definition)
            report.created.append(f"Object: {name}")
        report.print()
    finally:
        client.close()


if __name__ == "__main__":
    main_error_boundary(main)
