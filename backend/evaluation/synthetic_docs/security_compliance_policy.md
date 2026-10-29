# Enterprise Security & Compliance Policy
Document ID: SEC-POL-2026-B
Classification: Confidential - Internal Only

## 1. Cryptographic Standards
All corporate systems and SaaS applications must adhere to modern cryptographic safeguards:
- **Data at Rest**: All databases, EBS volumes, and S3 buckets must be encrypted using AES-256 with AWS KMS customer-managed keys (CMK).
- **Data in Transit**: All external and internal service-to-service communication requires TLS version 1.3. Earlier versions (TLS 1.0, 1.1, 1.2) are permanently disabled.
- Hashing algorithms for authentication passwords must exclusively use bcrypt with a minimum work factor of 12.

## 2. Credential & Key Lifecycle
- **API Keys**: Production API keys and service tokens must be rotated every 90 days.
- **Session Timeout**: User dashboard web sessions must expire after 15 minutes of user inactivity.
- Multi-factor authentication (MFA) via FIDO2 WebAuthn or TOTP hardware keys is mandatory for all employee accounts.

## 3. Data Retention & Audit Logging
- **Audit Logs**: Centralized audit trails (CloudTrail, VPC Flow logs, access logs) must be retained for exactly 365 days in tamper-proof S3 buckets with Object Lock in Compliance mode.
- Access to raw audit logs requires approval from both the Chief Information Security Officer (CISO) and the Lead Compliance Auditor.
- Automated daily integrity checksums (SHA-512) are calculated and published to an immutable ledger.
