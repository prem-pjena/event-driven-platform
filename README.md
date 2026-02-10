# Event-Driven Transaction, Analytics & Notification Platform

A production-grade, correctness-first backend system inspired by real-world architectures used at Amazon, Razorpay, Stripe, and Uber. This project demonstrates how to design and operate a distributed, event-driven backend where client-facing APIs are deterministic, retry-safe, and latency-isolated, while all side effects (payments, analytics, notifications) are executed asynchronously and independently.

The system is intentionally designed to reflect how large-scale backend systems evolve in production. Each layer was added only after the previous layer was made correct, observable, and failure-safe. The emphasis is on system design, idempotency, failure handling, and operational correctness rather than superficial feature count.


====================================================================
SYSTEM ARCHITECTURE (IMPLEMENTED & VERIFIED IN AWS)
====================================================================

Client
  |
  | HTTPS (REST)
  v
API Gateway (HTTP API)
  |
  | Lambda Invoke
  v
API Lambda (FastAPI + Mangum)
  |
  | Domain Events (Intent Only)
  v
Amazon EventBridge (Custom Event Bus)
  |
  | Fan-out
  v
Amazon SQS Queue
  |
  | Event Source Mapping
  v
Worker Lambda (Async, Non-HTTP)
  |
  | Redis (Locks, Idempotency, Rate Limits)
  | Database Writes / External Calls
  v
PostgreSQL (RDS, Private Subnet)
  |
  v
Outcome Events (EventBridge)

Key Architectural Property:
Client latency is fully isolated from execution. API correctness is never impacted by worker failures, retries, or downstream outages.


====================================================================
DESIGN GOALS
====================================================================

- Deterministic, retry-safe APIs
- No side effects in synchronous request path
- Asynchronous execution for resilience and scale
- Effectively-once semantics over at-least-once delivery
- Explicit failure handling at every boundary
- Cloud-native primitives over custom infrastructure
- Infrastructure defined as code
- Production-grade patterns suitable for FAANG-style systems


====================================================================
SYNCHRONOUS FLOW — PAYMENT CREATION (API PATH)
====================================================================

Client                 API Lambda
  |                        |
  | POST /payments         |
  |----------------------->|
  |                        | Validate request
  |                        | Require Idempotency-Key
  |                        | Persist intent
  |                        | Emit domain event
  |                        |
  | HTTP 202 Accepted      |
  |<-----------------------|

Properties:
- No external calls in API execution path
- No payment execution in API
- Idempotency enforced at API boundary
- Deterministic behavior under retries
- API Lambda uses Mangum handler only (Lambda-safe)
- API returns immediately after intent validation


====================================================================
ASYNCHRONOUS FLOW — PAYMENT EXECUTION (WORKER PATH)
====================================================================

EventBridge        SQS Queue        Worker Lambda        Redis        PostgreSQL
     |                |                  |                |                |
     | Emit event     |                  |                |                |
     |--------------->|                  |                |                |
     |                | Deliver message  |                |                |
     |                |----------------->|                |                |
     |                |                  | Acquire lock   |                |
     |                |                  |--------------->|                |
     |                |                  | Execute logic  |                |
     |                |                  | Update DB      |--------------->|
     |                |                  | Emit outcome   |                |
     |                |                  |-------------------------------> EventBridge

Properties:
- At-least-once delivery via SQS
- Effectively-once execution via Redis locks + DB state checks
- Terminal state committed before emitting outcome events
- Worker Lambda has no HTTP surface
- Retries are safe and deterministic


====================================================================
FAILURE SCENARIO — WORKER FAILURE (RETRY SAFE)
====================================================================

Worker Lambda
     |
     | Exception / Timeout
     v
Exception thrown
     |
     v
SQS message NOT deleted
     |
     v
Automatic retry
     |
     +--> Payment still PENDING → retry allowed
     |
     +--> Payment terminal → safe no-op

Guarantees:
- No double charging
- No partial state commits
- Deterministic retries
- Poison messages isolated using DLQ


====================================================================
FAILURE SCENARIO — DUPLICATE CLIENT REQUEST
====================================================================

Client retries request
     |
     v
Same Idempotency-Key
     |
     v
API Lambda
     |
     v
Original request re-validated
     |
     v
No duplicated execution

Guarantees:
- Client retries are always safe
- API behavior is deterministic
- Downstream execution never duplicated


====================================================================
REDIS — DISTRIBUTED COORDINATION LAYER (PRODUCTION-GRADE)
====================================================================

Redis is used strictly as a distributed coordination and correctness layer, never as a primary datastore. The system remains correct even if Redis becomes unavailable.

Infrastructure:
- AWS ElastiCache Redis cluster
- Deployed in private subnets
- Security group allows access only from Lambda
- Endpoint stored in AWS Secrets Manager
- No public access

Application Integration:
- Async Redis client
- Redis-backed idempotency keys with TTL
- Redis-based distributed locks using SET NX EX
- Ownership tokens prevent accidental lock release
- TTLs prevent deadlocks
- Graceful fallback to database if Redis is unavailable

Advanced Redis Usage:
- Distributed locking for worker execution
- Idempotency enforcement across retries
- Token-bucket rate limiting primitives
- Read-model caching hooks (prepared for scale)
- Redis failures never compromise correctness (fail-open design)


====================================================================
CORE CAPABILITIES (IMPLEMENTED & VERIFIED)
====================================================================

- Asynchronous, non-blocking API design using FastAPI
- Idempotency-first API contract
- Strict separation of intent handling and execution
- Event-driven architecture using EventBridge + SQS
- Retry-safe background workers
- Distributed coordination using Redis
- Effectively-once semantics built on top of at-least-once delivery
- Failure isolation across API, workers, and consumers
- Infrastructure as Code using Terraform
- Fully containerized Lambdas with separate images
- Clean handler separation (API vs Worker)
- Lambda-safe async execution (single event loop per invocation)
- Async SQLAlchemy without cross-loop contamination
- Explicit engine lifecycle management per worker invocation
- Schema-tolerant event consumption
- End-to-end execution verified in real AWS


====================================================================
TECH STACK
====================================================================

Backend:
- FastAPI (async)
- Pydantic
- SQLAlchemy (async)

Data:
- PostgreSQL (AWS RDS)
- Redis (AWS ElastiCache)

Cloud & Infrastructure:
- AWS Lambda (API + Worker)
- API Gateway (HTTP API)
- Amazon EventBridge
- Amazon SQS
- Docker (multi-image setup)
- Terraform (Infrastructure as Code)

Observability:
- Structured logging
- Correlation-friendly logs
- CloudWatch Logs


====================================================================
PROJECT STRUCTURE (CURRENT)
====================================================================

.
├── alembic
├── app
│   ├── api
│   │   └── routes
│   ├── core
│   │   ├── redis.py
│   │   ├── locks.py
│   │   ├── rate_limit.py
│   │   └── logging.py
│   ├── events
│   ├── services
│   ├── shared
│   └── workers
│       ├── payment_worker.py
│       ├── sqs_worker.py
│       └── db
├── infra
│   └── terraform
├── Dockerfile.api
├── Dockerfile.worker
├── docker-compose.yml
├── locustfile.py
└── README.md


====================================================================
DEPLOYMENT STATUS
====================================================================

Completed and verified in AWS:
- API and Worker Lambdas split correctly
- Separate Docker images per Lambda
- Correct handlers per image
- API Lambda uses Mangum only
- Worker Lambda triggered only by SQS
- Redis locking and idempotency verified
- EventBridge → SQS → Worker flow verified
- Payment retries validated under failure
- Alembic migrations applied safely
- End-to-end execution verified with real AWS resources


====================================================================
DESIGN PRINCIPLES
====================================================================

- Correctness over convenience
- Idempotency-first APIs
- Asynchronous execution for resilience
- Deterministic retries
- Failure isolation
- Distributed coordination via Redis
- Cloud-native primitives
- Infrastructure defined as code


====================================================================
AUTHOR NOTES
====================================================================

This project is intentionally built to reflect real backend engineering standards rather than tutorial shortcuts. Each architectural decision mirrors patterns used in production systems at scale. The goal is to demonstrate deep understanding of system design, idempotency, failure handling, and operational correctness expected from strong backend engineers applying for SDE-1 roles.
