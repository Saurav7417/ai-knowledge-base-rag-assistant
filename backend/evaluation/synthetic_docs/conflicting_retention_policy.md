# Special Regional Data Privacy & Retention Policy
Document ID: PRIV-REG-2026-EU
Authority: European Data Protection Officer

## 1. Audit Log Purge Schedule
Under European General Data Protection Regulation (GDPR) Article 17 (Right to Erasure) and internal cloud storage cost reduction initiatives:
- All raw audit logs, customer IP access logs, and application tracing events must be completely destroyed and purged after exactly 90 days.
- Retaining raw audit records beyond 90 days without documented judicial subpoena constitutes a regulatory violation.
- Aggregated anonymized monthly summaries may be retained for 3 years.

## 2. Customer Personal Data Erasure
- Customer account deletion requests must be honored across all read replicas within 72 hours of submission.
- Backups containing personal identifiers are aged out on a rolling 30-day snapshot schedule.
