# Event-Driven Transaction & Notification Platform

A production-grade backend system inspired by Razorpay- and Amazon-style event-driven architectures, designed with a strong focus on correctness, reliability, security, idempotency, asynchronous processing, observability, and cloud readiness.

This platform demonstrates real-world backend engineering practices including async APIs, idempotent payment workflows, decoupled background processing, retry-safe execution, secure API boundaries, event-driven fan-out, batch analytics, infrastructure as code, CI/CD automation, load testing, and production-grade observability — all critical for high-scale fintech and e-commerce systems.

The system is intentionally designed so that client-facing APIs remain fast and resilient, while all side effects (payments, notifications, analytics) are handled asynchronously, independently, and safely.


Architecture (Conceptual Flow)

Client  
→ Authenticated API Layer (FastAPI)  
→ Persistent Store (PostgreSQL)  
→ Event Abstraction Layer  
→ Asynchronous Workers  
→ External Systems (Payment Gateway / Email / SMS)  
→ Batch Analytics Jobs  


Core Capabilities

- Asynchronous, non-blocking API design
- Idempotent payment creation using request keys and database constraints
- Clear separation between API intent handling and execution via workers
- Retry-safe and failure-tolerant payment processing
- Event-driven fan-out for notifications and analytics
- Effectively-once processing semantics on top of at-least-once delivery
- Secure API boundaries with authentication and authorization
- Per-user abuse prevention, replay protection, and rate limiting
- Batch analytics for business and performance visibility
- Infrastructure, deployment, and observability readiness
- Designed for scalability, retries, monitoring, and dead-letter handling


Current System Behavior

- All client-facing endpoints require authenticated requests
- Payment requests are accepted synchronously and persisted with status = PENDING
- Each payment request requires an Idempotency-Key to guarantee safe retries
- Duplicate requests return the original persisted payment response
- Payment execution is handled asynchronously by background workers
- Workers are idempotent and provide effectively-once processing semantics
- Terminal states (SUCCESS / FAILED) are committed before any retries
- Payment outcome events are emitted only after successful database commits
- Events carry unique event identifiers to enable downstream deduplication
- Notifications (Email and SMS) are triggered asynchronously from payment events
- Notification delivery runs in parallel and is retried independently
- Notification failures never affect payment correctness
- Analytics are computed via scheduled batch jobs using persisted data
- Business metrics are pre-aggregated and stored for fast, reliable reads
- Internal execution paths simulate cloud infrastructure and are never exposed to untrusted callers


Security & Abuse Prevention

- JWT-based authentication to identify and verify API callers
- Role-based access control (RBAC) to restrict sensitive and internal operations
- Per-user rate limiting to prevent abuse and brute-force attacks
- Replay attack protection using mandatory idempotency keys
- Database-enforced uniqueness guarantees as the final guardrail
- Short-lived credentials and strict authorization checks to reduce blast radius


Notifications

- Payment success and failure events trigger downstream notification workers
- Email and SMS delivery are executed asynchronously and in parallel
- Notification workers are idempotent at the event level
- Duplicate event deliveries are safely ignored using event deduplication
- Failures are retried automatically using queue semantics
- Poison messages are isolated via dead-letter queue patterns
- Notification failures are fully isolated from payment correctness


Analytics & Observability

- Analytics are computed using batch jobs, not real-time API paths
- Metrics include:
  - Daily transaction volume
  - Successful and failed payment counts
  - Failure rate
  - Average end-to-end payment processing time
- Analytics are computed using Pandas and stored in a dedicated analytics table
- Pre-aggregated metrics enable fast dashboards and historical trend analysis
- Structured logging is used across API, workers, and analytics jobs
- Business-level logs capture outcomes, latency, and failure signals
- Correlation IDs enable tracing requests across asynchronous boundaries
- Load testing validates system behavior under concurrent traffic


Tech Stack

Backend
- FastAPI (async)
- Pydantic
- SQLAlchemy (async)

Data Layer
- PostgreSQL

Architecture & Reliability
- Event-driven design principles
- Idempotency enforced at API, database, worker, and event levels
- Retry-safe worker logic with explicit transaction boundaries
- Event-based fan-out for independent downstream consumers
- Failure isolation between correctness and side effects

DevOps, Infrastructure & Observability
- Dockerized application for consistent runtime environments
- CI pipeline using GitHub Actions for automated validation
- Infrastructure as Code using Terraform (queues, retries, DLQs)
- Environment-based configuration using .env files
- Structured logging and request correlation
- Load testing using Locust
- Cloud-ready design aligned with AWS managed services


API Example

Create Payment  
POST /payments/

Headers:  
Authorization: Bearer <JWT>  
Idempotency-Key: <uuid>

Body:
{
  "user_id": "uuid",
  "amount": 1000,
  "currency": "INR"
}

Behavior:
- API authenticates and authorizes the caller
- API responds immediately without calling external services
- Payment is persisted with status = PENDING
- Repeated requests with the same Idempotency-Key return the original payment
- Payment execution, notifications, and analytics are handled asynchronously


Local Development

Start PostgreSQL:
docker compose up -d

Run the API:
uvicorn app.main:app --reload

API Documentation:
http://127.0.0.1:8000/docs


Key Design Decisions

- Idempotency-first design prevents double charging and supports safe retries
- Authentication and authorization enforce strict trust boundaries
- Rate limiting protects the system from abuse and denial-of-service
- Asynchronous processing isolates client latency from external service failures
- Payment correctness is never dependent on notifications or analytics
- Workers commit terminal states before retrying to ensure correctness
- Persisted timestamps enable accurate latency and performance analytics
- Event-level deduplication ensures effectively-once downstream processing
- Database constraints act as the final guardrail for data integrity
- Infrastructure and deployment are reproducible via code
- Observability is built in through logs, metrics, tracing, and load testing


Planned Enhancements

- AWS Lambda-based deployment for API and workers
- EventBridge for event routing
- SQS with Dead Letter Queues (DLQ) for reliable background processing
- Redis-backed distributed rate limiting and caching
- Metrics dashboards and alerting
- Distributed tracing and centralized log aggregation
- Secure secret management using cloud-native services
- Progressive deployments (blue-green / canary)


Author Notes

This project is intentionally designed to mirror real-world backend systems used in large-scale fintech and e-commerce platforms, with a strong emphasis on correctness, security, reliability, observability, and system design trade-offs rather than superficial feature count.
