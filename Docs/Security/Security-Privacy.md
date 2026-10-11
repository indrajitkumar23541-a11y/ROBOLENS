# ROBOLENS — Security & Privacy

> **Purpose:** Protect user accounts, recorded videos, annotations, and robotics training datasets from unauthorized access or misuse.

## 1. Authentication & Authorization

- Use short-lived access tokens and revocable refresh tokens.
- Store passwords using a secure password-hashing algorithm such as Argon2id.
- Enforce role-based and resource-level permissions.
- Allow users to access only their authorized submissions and data.
- Restrict administrative, reviewer, and enterprise dataset permissions.
- Require multi-factor authentication for privileged accounts where supported.

## 2. Data Encryption

- Enforce HTTPS/TLS for all production API communication.
- Encrypt databases, backups, and object storage at rest.
- Store encryption keys and secrets in a secrets manager.
- Never commit API keys, passwords, tokens, or private credentials to Git.
- Rotate compromised credentials and encryption keys according to policy.

## 3. Video Privacy & Consent

- Obtain explicit, informed consent before collecting and processing user recordings.
- Explain intended use, storage, retention, sharing, and licensing.
- Keep original videos in private object storage.
- Use short-lived, access-controlled upload and download URLs.
- Apply appropriate safeguards for faces, voices, location metadata, and other identifying information.
- Do not publish or sell personal data outside the permissions and agreements covering its use.

## 4. API & Upload Security

- Validate every request on the backend.
- Apply rate limits to authentication, uploads, and sensitive endpoints.
- Verify upload ownership, file signatures, size limits, and checksums.
- Reject unsupported, corrupted, or suspicious files.
- Scan uploaded content where appropriate.
- Prevent unauthorized access to other users' submissions and organization resources.
- Use idempotency controls for retryable operations.

## 5. Data Retention & Deletion

- Define retention periods for raw videos, derived files, account data, and logs.
- Provide a documented process for eligible account and data-deletion requests.
- Delete or anonymize data according to applicable law, consent, and contractual obligations.
- Propagate approved deletions to derived assets and datasets where required.
- Document backup-expiration and restoration procedures.
- Do not promise immediate removal from immutable backups; define and communicate the applicable backup lifecycle.

## 6. Audit Logging

Record security-relevant events, including:

- Authentication successes and failures.
- Permission and role changes.
- Sensitive video and dataset access.
- Consent changes and deletion requests.
- Dataset exports and administrative actions.

Never log passwords, access tokens, secret keys, or unnecessary sensitive video content.

Protect audit logs from unauthorized modification and restrict access to authorized personnel.

## 7. Infrastructure Security

- Run services with least-privilege permissions.
- Keep dependencies and container images updated.
- Use separate development, staging, and production environments.
- Restrict database and Redis access to trusted services.
- Apply network controls and secure configuration defaults.
- Back up critical data and regularly test recovery.
- Run dependency, container, and vulnerability scans in CI/CD.

## 8. Security Incident Response

When a security incident occurs:

1. Detect and assess the incident.
2. Contain affected accounts, services, or credentials.
3. Preserve relevant evidence and audit logs.
4. Investigate the root cause and impact.
5. Restore services securely and rotate compromised secrets.
6. Notify affected parties and authorities when required.
7. Document lessons learned and implement preventive fixes.

Maintain a clear incident-response owner and escalation process.

## 9. Security Responsibilities

- **Mobile app:** Secure token handling, minimal permissions, and safe local storage.
- **FastAPI backend:** Authentication, authorization, validation, and access enforcement.
- **PostgreSQL:** Least-privilege database roles, backups, and protected credentials.
- **Object storage:** Private access, scoped upload permissions, and controlled downloads.
- **AI workers:** Restricted media access and isolated processing environments.
- **Dataset delivery:** Permission checks, licensing validation, and export auditing.

## 10. Implementation Checklist

- [ ] Authentication and authorization tests pass.
- [ ] Private videos cannot be accessed without permission.
- [ ] Consent is checked before processing and dataset release.
- [ ] Secrets are excluded from source control and logs.
- [ ] Encryption and backup recovery are verified.
- [ ] Data deletion and retention workflows are tested.
- [ ] Security-relevant actions are audited.
- [ ] Dependency and vulnerability checks are enabled.
- [ ] Incident-response procedures are documented.

**Security principle:** Privacy, consent, and access control must be enforced by the backend and infrastructure—not merely by the mobile app interface.

**Status:** Specification defined; implementation and security testing required before production launch.
