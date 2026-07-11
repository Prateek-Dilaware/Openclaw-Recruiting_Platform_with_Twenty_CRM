# API Contract

This document lists the REST API contracts between the frontend and backend.

## Endpoints

### Jobs
- `POST /api/v1/jobs` - Create a job posting from JD text.
- `GET /api/v1/jobs` - List jobs.

### Candidates
- `POST /api/v1/candidates` - Import candidates.
- `GET /api/v1/candidates/{id}` - Get candidate profile.
