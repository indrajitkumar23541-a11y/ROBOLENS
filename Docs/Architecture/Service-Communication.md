# ROBOLENS — Service Communication

> **Purpose:** Define how ROBOLENS backend services communicate reliably, securely, and efficiently.

## 1. Communication Strategy

ROBOLENS uses two communication patterns:

- **Synchronous:** REST APIs for requests that need an immediate response.
- **Asynchronous:** Durable workflows and events for long-running tasks such as video processing and dataset generation.

**Technology:** FastAPI, REST/JSON, Temporal, PostgreSQL, and Redis.

## 2. When to Use Each Pattern

| Operation | Communication |
|---|---|
| Login and profile requests | REST API |
| Fetch available tasks | REST API |
| Create a submission | REST API |
| Request a video upload session | REST API |
| Start video processing | Durable workflow |
| Run AI inference | Background worker |
| Notify processing completion | Event/workflow activity |
| Approve a dataset release | Authorized API + workflow |
| Send push notifications | Background job |

Avoid making mobile users wait for AI processing to finish before responding to their initial API request.

## 3. Video Processing Flow

1. The mobile app requests an upload session.
2. The Media Service authorizes the upload.
3. The app uploads the video to private object storage.
4. The backend verifies the uploaded file and checksum.
5. The Submission Service records the valid submission.
6. A durable workflow starts processing.
7. Workers validate, preprocess, and analyze the video.
8. Annotation and quality results are persisted.
9. Required human review takes place.
10. Approved data becomes eligible for dataset versioning.
11. The app receives updated status through polling or push notifications.

## 4. Service Ownership

Each service owns its data and business rules.

- Identity Service: accounts and authentication.
- Task Service: task definitions and eligibility.
- Submission Service: submission lifecycle.
- Media Service: uploads and media metadata.
- Processing Service: workflow coordination.
- Annotation Service: annotations and provenance.
- Quality Service: quality checks and review decisions.
- Dataset Service: dataset versions and membership.
- Export Service: authorized dataset exports.
- Notification Service: user notifications.

Services must not directly modify another service's private database tables. Use documented APIs or events.

## 5. Reliability Rules

- Use timeouts for network requests.
- Retry transient failures with bounded exponential backoff.
- Make retryable operations idempotent.
- Assign unique identifiers to jobs and events.
- Persist important state transitions.
- Send exhausted jobs to a recoverable failure state.
- Do not retry invalid files or permanent validation errors indefinitely.
- Use transactional outbox or an equivalent reliable publishing pattern when database updates must trigger events.

## 6. Event Standards

Every internal event should include:

- `event_id`: Unique event identifier.
- `event_type`: Event name.
- `event_version`: Schema version.
- `occurred_at`: UTC timestamp.
- `correlation_id`: Links related operations.
- `aggregate_id`: Related submission, task, or dataset ID.
- `payload`: Minimum necessary event data.

Example event types:

- `SubmissionCreated`
- `MediaValidated`
- `ProcessingCompleted`
- `QualityReviewCompleted`
- `DatasetVersionReleased`

Events must not contain passwords, access tokens, or unnecessary personal data.

## 7. Duplicate Events & Ordering

- Assume events may be delivered more than once.
- Deduplicate using event IDs or stable business-operation keys.
- Enforce database uniqueness constraints where appropriate.
- Do not assume events arrive in order.
- Check current state before applying state-changing operations.
- Reject invalid status transitions.

## 8. Security

- Authenticate service-to-service requests.
- Authorize every sensitive operation.
- Keep internal endpoints private.
- Use TLS where required by the deployment environment.
- Protect credentials and signing keys.
- Validate event schemas and upload references.
- Record security-relevant actions without exposing secrets.

## 9. Observability

Propagate correlation and trace IDs across API requests, workflows, and worker jobs.

Monitor:

- Request latency and error rates.
- Workflow failures and retry counts.
- Queue and worker delays.
- Processing duration.
- Duplicate-event handling.
- Dataset release failures.

## 10. Implementation Principle

Start with REST APIs and Temporal-managed workflows. Add a dedicated message broker only when independent event streaming, throughput, or service decoupling requires it.

**Goal:** Reliable communication without unnecessary infrastructure complexity.
