# Validation

Before deployment or after a plugin/workflow upgrade:

1. Confirm metadata discovery finds all six Schema V2 objects.
2. In a non-production workspace, verify one informational `twenty_record_update` and re-read it.
3. Verify a workflow mutation requires approval and returns a run id.
4. Verify a failed/denied workflow does not directly alter a lifecycle field.
5. Record the tested plugin version, workflow version ids, and results outside candidate records.