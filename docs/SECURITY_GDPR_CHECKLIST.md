# Security & GDPR Compliance Checklist

## Security Checklist

### Transport Security
- [ ] TLS/HTTPS enabled on all public endpoints
- [ ] HTTP Strict Transport Security (HSTS) headers configured
- [ ] Secure cookies (HttpOnly, Secure, SameSite)
- [ ] Certificate auto-renewal (Let's Encrypt)

### Authentication & Authorization
- [ ] JWT access tokens with short lifetime (15 minutes)
- [ ] Refresh tokens stored in HttpOnly cookies
- [ ] Token rotation on refresh
- [ ] Password hashing with bcrypt/argon2 (cost factor ≥12)
- [ ] Account lockout after failed attempts
- [ ] Role-based access control (RBAC)
- [ ] Admin endpoints protected

### Input Validation & Sanitization
- [ ] Pydantic models for all request bodies
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] Path traversal prevention
- [ ] File upload validation (type, size)

### Rate Limiting & DDoS Protection
- [ ] Per-IP rate limiting (Redis-backed)
- [ ] Per-user rate limiting
- [ ] LLM endpoint rate limiting (cost protection)
- [ ] Request size limits

### Secrets Management
- [ ] No secrets in source code
- [ ] Environment variables for secrets
- [ ] Secrets in Vault/cloud secrets manager (production)
- [ ] Secret rotation capability
- [ ] `.env` files in `.gitignore`

### Security Headers
- [ ] Content-Security-Policy (CSP)
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] Referrer-Policy
- [ ] Permissions-Policy

### Logging & Monitoring
- [ ] No PII in logs (hash/pseudonymize)
- [ ] Request ID tracing
- [ ] Security event logging (failed logins, permission denied)
- [ ] Log aggregation and alerting
- [ ] Audit trail for sensitive operations

### Infrastructure
- [ ] Container images from trusted sources
- [ ] No root in containers
- [ ] Network isolation (Docker networks)
- [ ] Database not exposed publicly
- [ ] Regular security scans (Snyk, Bandit)
- [ ] Dependency vulnerability scanning

---

## GDPR Compliance Checklist

### Lawful Basis & Consent
- [ ] Clear purpose for data collection documented
- [ ] Explicit consent obtained before processing
- [ ] Consent stored with timestamp
- [ ] Easy consent withdrawal mechanism
- [ ] Separate consents for different purposes

### Data Minimization
- [ ] Only necessary data collected
- [ ] Sensitive data identified and flagged
- [ ] Data retention periods defined
- [ ] Automatic data purge jobs

### User Rights Implementation

#### Right to Access (Article 15)
- [ ] API endpoint: `GET /user/{id}/export`
- [ ] Export includes all user data
- [ ] Machine-readable format (JSON)
- [ ] Response within 30 days

#### Right to Erasure (Article 17)
- [ ] API endpoint: `POST /user/{id}/delete`
- [ ] Data anonymization instead of hard delete (for audit)
- [ ] Vector embeddings removed from Qdrant
- [ ] Confirmation to user
- [ ] Response within 30 days

#### Right to Rectification (Article 16)
- [ ] User profile update endpoints
- [ ] Audit log of changes

#### Right to Data Portability (Article 20)
- [ ] Export in standard format
- [ ] Include attachments/files

### Data Protection Measures
- [ ] Encryption at rest (database, files)
- [ ] Encryption in transit (TLS)
- [ ] Access controls per user
- [ ] PII flagging in audit logs
- [ ] Pseudonymization where possible

### LLM-Specific Considerations
- [ ] User consent for chat logging
- [ ] LLM provider data processing agreements
- [ ] No PII sent to LLM without consent
- [ ] Model provider documented
- [ ] Accuracy claims documented

### Documentation
- [ ] Privacy policy accessible
- [ ] Data Processing Agreement (DPA) template
- [ ] Data Protection Impact Assessment (DPIA)
- [ ] Record of Processing Activities (ROPA)
- [ ] Breach notification procedure

### Third-Party Services
- [ ] LLM providers: Data processing agreements
- [ ] Analytics: GDPR-compliant (Langfuse self-hosted)
- [ ] Data residency requirements met
- [ ] Sub-processor list maintained

---

## Audit Status

| Category | Items Completed | Total | Status |
|----------|-----------------|-------|--------|
| Transport Security | 0 | 4 | Not Started |
| Auth & Authorization | 0 | 7 | Not Started |
| Input Validation | 0 | 5 | Not Started |
| Rate Limiting | 0 | 4 | Not Started |
| Secrets Management | 2 | 5 | In Progress |
| Security Headers | 0 | 5 | Not Started |
| Logging & Monitoring | 0 | 4 | Not Started |
| Infrastructure | 1 | 6 | In Progress |
| GDPR User Rights | 0 | 6 | Not Started |
| GDPR Data Protection | 0 | 5 | Not Started |

**Last Updated**: 2025-12-18
