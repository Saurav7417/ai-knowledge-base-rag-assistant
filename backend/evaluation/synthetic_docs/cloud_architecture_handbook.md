# Cloud Infrastructure & Distributed Architecture Handbook
Version: 3.4.0
Last Updated: 2026-03-15

## 1. Disaster Recovery Objectives
Our production cloud infrastructure across AWS and GCP enforces strict disaster recovery targets.
- **Recovery Time Objective (RTO)**: Maximum acceptable downtime is set to exactly 15 minutes.
- **Recovery Point Objective (RPO)**: Maximum allowable data loss window is set to 5 minutes.
Cross-region active-passive replication is automated via terraform modules in `us-east-1` (primary) and `us-west-2` (secondary).

## 2. Kubernetes Pod Autoscaling
The microservices fleet runs on Amazon EKS version 1.30.
- Horizontal Pod Autoscaler (HPA) metrics trigger when average CPU utilization exceeds 75% for 3 consecutive minutes.
- Memory scale-up occurs when container memory usage reaches 80% of allocated limits.
- The scale-down stabilization window is configured to 300 seconds to prevent thrashing.

## 3. Database Connection Pooling
PostgreSQL 16 instances utilize PgBouncer in transaction pooling mode.
- `default_pool_size` is fixed at 40 active connections per replica.
- `reserve_pool_size` is allocated 10 connections for traffic spikes.
- Client connection timeout is capped at 5000 milliseconds.
- Idle server connection timeout is set to 600 seconds.

## 4. Message Streaming & Dead Letter Queues
Apache Kafka clusters manage high-throughput event ingestion.
- The replication factor for all audit and financial topics is 3 with `min.insync.replicas=2`.
- Consumers that fail processing after 5 sequential retries automatically route messages to the Dead Letter Queue (`dlq-microservices-v1`).
- Messages in the DLQ have an automatic retention duration of 14 days before archival to Amazon S3 Glacier.
