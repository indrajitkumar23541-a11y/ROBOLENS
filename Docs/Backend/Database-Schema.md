# ROBOLENS — Database Schema

> **Purpose:** Define how ROBOLENS stores users, task videos, AI annotations, quality reviews, and datasets.

## 1. Database Technology

- **Database:** PostgreSQL
- **Cache:** Redis
- **Video Storage:** S3-compatible object storage
- **Backend:** Python + FastAPI

**Core rule:** PostgreSQL stores structured data and video metadata. Actual video files are stored in object storage, not directly inside database tables.

## 2. Core Database Tables

| Table | Purpose |
|---|---|
| `users` | Contributor and administrator accounts |
| `organizations` | Enterprise customers and research organizations |
| `organization_members` | Links users to organizations |
| `tasks` | Instructions for recording a specific activity |
| `submissions` | Records of videos submitted by contributors |
| `media_assets` | Video file locations, sizes, checksums, and upload status |
| `annotations` | AI-generated or human-corrected actions and objects |
| `quality_reviews` | Approval, rejection, and feedback on submissions |
| `consents` | User permissions and data usage agreements |
| `datasets` | Collections of approved training data |
| `dataset_versions` | Version history of datasets |
| `dataset_items` | Links approved submissions to dataset versions |
| `audit_logs` | Records important security and administrative actions |

## 3. Important Relationships

- One user can create multiple submissions.
- One task can receive multiple submissions.
- One submission can contain multiple media assets and annotations.
- One submission can have multiple quality-review records.
- One dataset can have multiple versions.
- Each dataset version can contain multiple approved submissions.

## 4. Essential Database Rules

- Every table must have a primary key.
- Use foreign keys to maintain valid relationships.
- Add indexes to frequently searched fields, such as user IDs, task IDs, statuses, and timestamps.
- Use unique constraints for email addresses and other fields that must be unique.
- Store timestamps in UTC.
- Track annotation provenance: `AI_GENERATED` or `HUMAN_VERIFIED`.
- Never include a submission in a dataset unless its required consent and quality checks are satisfied.
- Use soft deletion or controlled retention where required by privacy policies.

## 5. Submission Status Flow

`DRAFT → UPLOADING → PROCESSING → IN_REVIEW → APPROVED`

A submission may instead move to `REJECTED` or `FAILED`. Retries must not create duplicate submissions.

## 6. Data Integrity and Security

- Store passwords as secure hashes, never as plain text.
- Keep private video-storage URLs and access credentials protected.
- Enforce authorization in the FastAPI backend.
- Maintain an audit trail for sensitive actions.
- Use database migrations to track schema changes.
- Back up PostgreSQL and regularly test restoration.

## 7. Implementation Standard

This document defines the database blueprint for ROBOLENS. Before implementation, each table must have finalized column names, PostgreSQL data types, primary and foreign keys, constraints, indexes, and migration scripts.

**Design principle:** Keep the schema simple, secure, scalable, and easy to maintain. Add new tables only when a real product requirement needs them.
