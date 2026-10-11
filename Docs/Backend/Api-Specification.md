# ROBOLENS — API Specification

> **Purpose:** Define how the ROBOLENS Android/iOS mobile app, backend, and authorized dataset consumers communicate.

## 1. Technology

- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Authentication:** Short-lived access tokens + refresh tokens
- **Video Storage:** S3-compatible object storage
- **API Format:** REST + JSON
- **API Version:** `/api/v1`

All timestamps use UTC and ISO 8601 format.

## 2. API Standards

- Base path: `/api/v1`
- Use JSON for requests and responses, except direct media uploads.
- Require authentication for private resources.
- Validate all inputs on the server.
- Return consistent error responses.
- Use pagination for large lists.
- Make retryable operations idempotent where appropriate.
- Generate API documentation through FastAPI's OpenAPI support.

## 3. Authentication APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Authenticate a user |
| POST | `/auth/refresh` | Renew an access token |
| POST | `/auth/logout` | Revoke the current session |
| GET | `/users/me` | Get the current user's profile |
| PATCH | `/users/me` | Update permitted profile fields |

Passwords must be securely hashed. Refresh tokens must be protected, revocable, and never exposed in logs.

## 4. Task APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/tasks` | List available recording tasks |
| GET | `/tasks/{task_id}` | Get task instructions |
| GET | `/tasks/{task_id}/eligibility` | Check whether the user can participate |

Only tasks that are active and available to the authenticated user should be returned.

## 5. Submission and Upload APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/submissions` | Create a submission |
| GET | `/submissions` | List the user's submissions |
| GET | `/submissions/{id}` | Get submission details and status |
| POST | `/submissions/{id}/uploads` | Create an upload session |
| POST | `/uploads/{upload_id}/complete` | Finalize an upload |
| GET | `/uploads/{upload_id}` | Check upload status |
| POST | `/submissions/{id}/cancel` | Cancel an eligible submission |

### Upload lifecycle

1. The app creates a submission.
2. The backend checks task eligibility, permissions, and required consent.
3. The backend creates a short-lived upload session.
4. The app uploads video directly to private object storage.
5. The backend verifies the uploaded object, checksum, and file metadata.
6. The backend queues processing only after successful validation.

Use resumable or multipart uploads when supported. Do not trust client-provided file metadata without verification.

## 6. Processing and Review APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/submissions/{id}/processing` | Get processing status |
| GET | `/submissions/{id}/annotations` | View permitted annotations |
| GET | `/submissions/{id}/reviews` | View permitted review results |

Processing and review records must only be visible to authorized users. Contributor access to internal reviewer notes may be restricted.

## 7. Dataset APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/datasets` | List datasets available to the caller |
| GET | `/datasets/{id}` | Get dataset metadata |
| GET | `/datasets/{id}/versions` | List dataset versions |
| GET | `/datasets/{id}/versions/{version}` | Get version details |
| POST | `/datasets/{id}/exports` | Request an authorized dataset export |
| GET | `/exports/{export_id}` | Check export status |

Dataset access must be restricted by organization membership, permissions, licensing, and applicable consent. Export links must be short-lived and access-controlled.

## 8. Standard Response Format

**Success example**

    {
      "success": true,
      "data": {
        "submission_id": "sub_123",
        "status": "PROCESSING"
      },
      "request_id": "req_456"
    }

**Error example**

    {
      "success": false,
      "error": {
        "code": "INVALID_UPLOAD",
        "message": "The uploaded file could not be validated."
      },
      "request_id": "req_456"
    }

Do not expose stack traces, secrets, private storage paths, or sensitive personal data in errors.

## 9. Submission Statuses

`DRAFT → UPLOADING → PROCESSING → IN_REVIEW → APPROVED`

Alternative terminal or recovery states may include `REJECTED`, `FAILED`, and `CANCELLED`. Define allowed transitions centrally and reject invalid transitions.

## 10. Security Requirements

- Enforce role-based and resource-level authorization.
- Validate file types, sizes, checksums, and upload ownership.
- Rate-limit authentication and sensitive endpoints.
- Protect against replay, unauthorized access, and duplicate requests.
- Use HTTPS in production.
- Keep secrets in a secrets manager or protected environment configuration.
- Record security-relevant events without logging tokens or private media.
- Apply consent, retention, deletion, and export policies.
- Validate webhook signatures if external callbacks are introduced.

## 11. Testing and Documentation

- Generate OpenAPI documentation from FastAPI.
- Test successful, invalid, unauthorized, and expired-token requests.
- Test upload interruptions, retries, duplicate requests, and checksum failures.
- Test organization-level dataset access restrictions.
- Maintain versioned API contracts and automated integration tests.

**Implementation rule:** This specification defines the API contract. Final request/response models, permissions, validation rules, and database transactions must be implemented and tested before an endpoint is considered production-ready.
