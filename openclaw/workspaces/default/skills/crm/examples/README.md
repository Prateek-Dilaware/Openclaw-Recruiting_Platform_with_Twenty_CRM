# Examples

## Safe write

1. Read the application and confirm its id.
2. Discover `parsedResumeSummary` if not already known.
3. Call `twenty_record_update` with only `{ "parsedResumeSummary": "..." }`.
4. Re-read and report the stored summary.

## Workflow change

1. Read the application and current stage.
2. Inspect the Application Stage Transition workflow and current version.
3. Present the requested transition and obtain runtime approval.
4. Run the approved version; retain its workflow-run id.
5. Inspect the run and re-read the application. If it fails, report without patching `stage`.