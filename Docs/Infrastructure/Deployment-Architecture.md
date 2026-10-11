# ROBOLENS — Deployment Architecture

> **Purpose:** Define how ROBOLENS backend services, AI processing workers, database, and storage are deployed, monitored, and scaled.

## 1. Technology Stack

- **Mobile App:** Flutter + Dart (Android/iOS)
- **Backend API:** Python + FastAPI
- **Database:** PostgreSQL
- **Cache & Coordination:** Redis
- **Workflow Orchestration:** Temporal
- **Media Storage:** S3-compatible object storage
- **Video Processing:** Python, FFmpeg, OpenCV, PyTorch
- **Containers:** Docker
- **CI/CD:** GitHub Actions or an equivalent pipeline

**Architecture rule:** Start with a modular backend and separately scalable processing workers. Introduce additional services only when operational needs justify them.

## 2. Deployment Architecture

```text
ROBOLENS Mobile App
        |
     HTTPS/TLS
        |
  FastAPI Backend
        |
  ┌─────┼──────────┐
  |     |          |
PostgreSQL       Redis
  |
Metadata & State

FastAPI ──> Private Object Storage
                    |
              Processing Queue
                    |
             Temporal Workflows
                    |
          CPU / GPU Processing Workers
                    |
          Annotations & Quality Results
                    |
           Approved Dataset Releases
```

Redis supports caching and coordination; durable workflow state and processing progress must not depend on cache persistence alone.

## 3. Environments

Maintain three separate environments:

- **Development:** Local development, Docker Compose, test data.
- **Staging:** Production-like configuration for integration and release testing.
- **Production:** Protected infrastructure, real user data, monitoring, and backups.

Never use real user videos in development without explicit authorization and appropriate safeguards.

## 4. Containerization

Use Docker images for the FastAPI backend and processing workers.

- Pin dependency versions and use reproducible builds.
- Use multi-stage builds where practical.
- Run containers as non-root users.
- Keep secrets outside container images.
- Add health checks and resource limits.
- Keep CPU workers separate from GPU workers when their requirements differ.
- Use Docker Compose for local development; use managed container hosting or orchestration when production scale requires it.

## 5. CI/CD Pipeline

Every pull request should run:

1. Code formatting and linting.
2. Type checks where applicable.
3. Unit and integration tests.
4. Security and dependency scans.
5. Docker image build validation.
6. Database migration checks.

After approval and successful checks:

- Build and publish versioned container images.
- Deploy to staging.
- Run smoke and integration tests.
- Promote to production through an approved release process.
- Support rollback to a known-good application version.

Run database migrations as controlled deployment steps, with backups and a recovery plan for risky changes.

## 6. Database, Cache & Storage

**PostgreSQL**
- Use managed PostgreSQL when practical.
- Enable automated backups and point-in-time recovery where supported.
- Restrict network access and database privileges.
- Monitor connections, query latency, and storage capacity.

**Redis**
- Use for caching, rate limiting, and temporary coordination.
- Configure authentication and private network access.
- Never treat cached values as the sole source of critical durable state.

**Object Storage**
- Keep original videos and derived assets private.
- Use short-lived upload/download URLs.
- Apply encryption, lifecycle rules, and appropriate versioning.
- Validate uploads before triggering expensive AI processing.

## 7. Monitoring & Logging

Track:

- API availability and response latency.
- Error rates and authentication failures.
- Database health and connection usage.
- Upload success, failures, and storage usage.
- Workflow queue depth and processing duration.
- CPU/GPU utilization and worker failures.
- Dataset export failures and security events.

Use structured logs, metrics, alerts, and distributed tracing where appropriate. Never log secrets or unnecessary personal data.

## 8. Backup & Disaster Recovery

- Back up PostgreSQL on a defined schedule.
- Use point-in-time recovery where supported.
- Protect backups with encryption and restricted access.
- Define retention periods and recovery objectives.
- Test restoration regularly.
- Document recovery steps for database, object storage, and workflow infrastructure.
- Ensure backups and recovery procedures meet applicable consent and deletion requirements.

A backup is not considered reliable until restoration has been tested.

## 9. Scaling Strategy

Scale based on measured demand:

- **API:** Add instances behind a load balancer.
- **Database:** Optimize queries and indexes before considering read replicas.
- **Video Processing:** Add CPU workers as decoding demand grows.
- **AI Inference:** Add GPU workers when model workloads justify the cost.
- **Storage:** Scale through object storage capacity and lifecycle policies.
- **Workflow Processing:** Adjust worker concurrency and queue capacity.

Use resource limits and queue backpressure to prevent expensive video workloads from overwhelming the API or database.

## 10. Production Readiness Checklist

- [ ] HTTPS and secure configuration enabled.
- [ ] Separate staging and production environments.
- [ ] Automated tests and security checks in CI/CD.
- [ ] Database migrations reviewed and tested.
- [ ] Private object storage and controlled upload URLs.
- [ ] Monitoring, alerts, and health checks configured.
- [ ] Automated backups and successful restore tests.
- [ ] Worker retries, failure handling, and resource limits configured.
- [ ] Rollback and incident-response procedures documented.
- [ ] Secrets and permissions reviewed before release.

**Implementation principle:** Deploy the simplest reliable architecture first, measure actual usage, and scale individual components when evidence shows a need.

**Status:** Deployment specification defined; cloud provider selection, configuration, implementation, and production validation remain to be completed.
