# ROBOLENS — Data Processing Pipeline

> **Purpose:** Convert contributor-recorded videos into validated, traceable, robotics-training datasets.

## 1. Pipeline Overview

`Video Upload → Validation → Preprocessing → AI Analysis → Quality Checks → Human Review → Dataset Release`

**Technology:** Python, FFmpeg, OpenCV, PyTorch, Temporal, PostgreSQL, Redis, and private object storage.

## 2. Processing Stages

### Stage 1: Receive and Verify

- Confirm the upload has completed.
- Verify object ownership, file size, checksum, and supported format.
- Check task association and required consent.
- Reject corrupted, unauthorized, or invalid files.

**Output:** A verified media asset or a clear validation failure.

### Stage 2: Preprocess Video

- Read video metadata, duration, resolution, and frame rate.
- Extract frames at configured sampling intervals.
- Normalize timestamps and prepare model-compatible inputs.
- Detect decoding errors and unusable footage.
- Preserve the original video as an immutable source asset.

**Output:** Validated metadata and derived processing assets.

### Stage 3: AI Analysis

Use suitable computer-vision models to identify, where supported:

- Objects and relevant entities.
- Human activities and action segments.
- Action start/end timestamps.
- Object interactions and scene changes.
- Potentially incomplete or ambiguous recordings.

Example labels:

`pick_up(cup)` → `move(cup)` → `place(cup, table)`

These are predicted labels, not automatically verified ground truth.

### Stage 4: Generate Annotations

Store structured annotations with:

- Action or object label.
- Start and end timestamps.
- Model name and version.
- Confidence score, when available.
- Annotation source: `AI_GENERATED` or `HUMAN_VERIFIED`.
- Review status and correction history.

Do not overwrite original AI predictions when a human corrects them. Preserve provenance and version history.

### Stage 5: Quality Checks

Run automated checks for:

- Corrupted or incomplete video.
- Missing timestamps or invalid annotations.
- Duplicate or near-duplicate submissions.
- Low-quality, excessively blurred, or unusable footage.
- Inconsistent task labels.
- Missing consent or licensing requirements.

Each check must have defined thresholds and a recorded result.

**Possible outcomes:** `PASS`, `NEEDS_REVIEW`, or `FAIL`.

### Stage 6: Human Review

Send uncertain or policy-sensitive submissions to an authorized reviewer.

Reviewers can:

- Verify or correct annotations.
- Approve or reject submissions.
- Record rejection reasons.
- Flag privacy, safety, or quality concerns.

Maintain reviewer identity, decision time, and annotation revision history. Human review requirements depend on the intended dataset and its quality policy.

### Stage 7: Build Dataset

Only eligible, approved data can enter a releasable dataset.

- Group compatible submissions by task and dataset definition.
- Validate consent, licensing, and access restrictions.
- Create immutable dataset versions.
- Record the exact submission and annotation revisions included.
- Generate manifests and quality reports.
- Provide authorized consumers with controlled API access or export links.

Dataset versioning must make releases reproducible.

## 3. Workflow and Status Management

Use Temporal or an equivalent durable workflow engine to coordinate long-running jobs.

Example processing states:

`QUEUED → VALIDATING → PREPROCESSING → AI_ANALYSIS → QUALITY_CHECK → IN_REVIEW → APPROVED`

Alternative states:

- `REJECTED`
- `FAILED`
- `CANCELLED`
- `RETRY_PENDING`

Persist state transitions and error categories. Retry transient failures with bounded exponential backoff. Do not endlessly retry invalid files or permanent failures.

## 4. Reliability Rules

- Make each stage idempotent where possible.
- Use unique job identifiers and deduplication keys.
- Keep processing artifacts in versioned, private storage.
- Separate CPU-intensive video decoding from GPU-intensive model inference.
- Limit file size, duration, frame count, and resource consumption.
- Track model versions and processing configuration.
- Support safe retries without duplicating dataset entries.
- Send exhausted jobs to a monitored failure queue or equivalent recovery process.

## 5. Privacy and Data Governance

- Process only data covered by valid consent and permitted usage.
- Detect and handle potentially identifying information according to policy.
- Restrict raw video access to authorized services and reviewers.
- Apply documented retention, deletion, and access-revocation procedures.
- Keep audit records for sensitive access and dataset releases.
- Ensure downstream datasets respect consent, licensing, and contractual restrictions.

## 6. Robotics Data Limitations

Standard smartphone RGB video can support visual observations and estimated action labels. It does **not** inherently provide:

- Exact 3D object trajectories.
- Robot joint positions or joint states.
- Force, torque, or tactile measurements.
- Guaranteed ground-truth action labels.

If a dataset requires these signals, use suitable additional sensors, calibrated capture methods, or explicitly validated estimation techniques. Mark estimated values separately from measured ground truth.

## 7. Monitoring and Metrics

Track:

- Upload validation success rate.
- Processing duration and failure rate.
- Queue depth and retry count.
- AI annotation coverage and review correction rate.
- Quality-check pass rate.
- Human-review turnaround time.
- Approved dataset volume and release integrity.

Alert on sustained failures, growing queues, storage problems, and unexpected processing delays.

## 8. Definition of Done

A submission is ready for dataset inclusion only when:

- The media file is validated.
- Required processing has completed.
- Required quality checks have passed.
- Required human review is complete.
- Consent and licensing requirements are satisfied.
- Annotation provenance is recorded.
- The submission is linked to a traceable dataset version.

**Implementation principle:** Every processing result must be traceable to its source video, processing configuration, model version, annotation revision, and review decision.
