# Scheduling Contract

## Required inputs

- Application and interview identifiers.
- Round/type, duration, interviewer(s), and decision owner.
- Candidate and interviewer availability with source and timezone.
- Requested lifecycle action: schedule, reschedule, or cancel.

## Integration rule

Calendar access is supplied by an approved MCP server when available. The CRM workflow remains the authority for recruiting lifecycle state. A calendar event is not proof of an approved CRM transition, and a CRM transition is not proof that an external invitation was delivered.