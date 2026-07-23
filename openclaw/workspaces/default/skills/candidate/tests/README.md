# Validation

1. Test exact and ambiguous lookup in a non-production workspace.
2. Test duplicate detection before candidate creation.
3. Verify only intended non-state fields change after update.
4. Verify merge requests produce no mutation.
5. Verify summaries identify source record ids and do not invent timeline events.