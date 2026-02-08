# Event-Driven Transaction & Notification Platform

A production-grade backend system inspired by Razorpay- and Amazon-style event-driven architectures, built to demonstrate correctness-first backend engineering, asynchronous processing, idempotency, and cloud-native execution using AWS.

The system is intentionally designed so that client-facing APIs remain fast, deterministic, and retry-safe, while all execution side effects (payments, notifications, analytics) are handled asynchronously and independently via background workers.

This repository reflects a real-world, incremental build of a distributed backend system, with explicit separation between completed components and planned system design upgrades.


====================================================
SYSTEM ARCHITECTURE (CURRENT – IMPLEMENTED)
====================================================

Client
  |
  |  HTTPS (REST)
  v
API Gateway (HTTP API)
  |
  |  Lambda Invoke
  v
API Lambda (FastAPI + Mangum)
  |
  |  Async DB Write
  v
PostgreSQL (RDS, Private Subnet)
  |
  |  Domain Event
  v
EventBridge
  |
  |  Fan-out
  v
SQS Queue
  |
  |  Event Source Mapping
  v
Worker Lambda
  |
  |  External Calls
  v
Payment Gateway / Notifications


Key Property:
Client latency is fully isolated from payment execution and downstream side effects.


====================================================
SEQUENCE DIAGRAM — PAYMENT CREATION (SYNC PATH)
====================================================

Client           API Lambda            PostgreSQL
  |                  |                     |
  | POST /payments   |                     |
  |----------------->|                     |
  |                  | Validate request    |
  |                  | Require idempotency|
  |                  | Insert payment      |
  |                  | status = PENDING    |
  |                  |-------------------->|
  |                  |                     |
  | 201 Created      |                     |
  |<-----------------|                     |


Properties:
- No external calls in API path
- Deterministic and retry-safe
- Idempotency guaranteed by request key + DB constraints
- API Lambda uses Mangum handler only (Lambda-safe)


====================================================
SEQUENCE DIAGRAM — ASYNCHRONOUS EXECUTION (WORKER)
====================================================

PostgreSQL     EventBridge        SQS Queue        Worker Lambda
     |               |                |                  |
     | Payment row   |                |                  |
     |-------------->|                |                  |
     |               | Emit event     |                  |
     |               |--------------->|                  |
     |               |                | Deliver message  |
     |               |                |----------------->|
     |               |                |                  |
     |               |                | Process payment  |
     |               |                | Update DB        |
     |               |                | Emit outcome     |
     |               |                |-----------------> EventBridge


Properties:
- At-least-once delivery via SQS
- Effectively-once processing via state checks
- Terminal state committed before emitting outcome events
- Worker Lambda uses SQS handler only (no HTTP / Mangum)


====================================================
FAILURE SCENARIO — WORKER FAILURE (RETRY SAFE)
====================================================

Worker Lambda
     |
     | Gateway timeout / exception
     v
Exception thrown
     |
     v
SQS does NOT delete message
     |
     v
Message retried automatically
     |
     +--> Payment still PENDING → retry allowed
     |
     +--> Payment terminal → safe no-op


Guarantees:
- No double charging
- No inconsistent payment state
- Retries are safe, bounded, and deterministic


====================================================
FAILURE SCENARIO — DUPLICATE CLIENT REQUEST
====================================================

Client retries request
     |
     v
Same Idempotency-Key
     |
     v
API Lambda
     |
     v
DB lookup finds existing payment
     |
     v
Original response returned


Guarantees:
- Exactly-once payment creation
- Safe client retries
- No duplicate records


====================================================
CORE CAPABILITIES (IMPLEMENTED UP TO PHASE 1.2)
====================================================

- Asynchronous, non-blocking API design using FastAPI
- Idempotent payment creation enforced via Idempotency-Key + DB constraints
- Clear separation between API intent handling and execution logic
- Background payment processing using SQS-triggered worker Lambda
- Retry-safe worker execution with terminal state persistence
- Event-driven architecture using EventBridge + SQS fan-out
- Effectively-once semantics on top of at-least-once delivery
- Failure isolation between API, payments, and downstream consumers
- Infrastructure as Code using Terraform
- Fully containerized Lambdas using separate Docker images
- Clean Lambda handler separation (API vs Worker)
- Lambda-safe execution (no async coroutine returned to runtime)


====================================================
CURRENT SYSTEM BEHAVIOR (VERIFIED END-TO-END)
====================================================

- Clients call POST /payments
- API Lambda:
  - Uses Mangum handler only
  - Validates request
  - Requires Idempotency-Key
  - Persists payment with status = PENDING
  - Returns response immediately (HTTP 201)
- Duplicate requests return the original persisted payment
- API Lambda does NOT execute payments or publish events
- Event emission and execution happen asynchronously
- Worker Lambda:
  - Triggered only by SQS
  - Consumes EventBridge-shaped events
  - Executes payment logic
  - Transitions payment to SUCCESS or FAILED
  - Commits terminal state before emitting outcome events
- Worker failures trigger automatic retries via SQS
- No async coroutine is ever returned directly to Lambda runtime
- Payment correctness is never affected by retries or failures


====================================================
TECH STACK
====================================================

Backend:
- FastAPI (async)
- Pydantic
- SQLAlchemy (async)

Data:
- PostgreSQL (AWS RDS)

Cloud & Infrastructure:
- AWS Lambda (API + Worker split)
- API Gateway (HTTP API)
- Amazon EventBridge
- Amazon SQS
- Docker (separate images per Lambda)
- Terraform (IaC)

Observability:
- Structured logging
- Correlation IDs
- CloudWatch Logs


====================================================
API EXAMPLE (WORKING)
====================================================

POST /payments

Headers:
Authorization: Bearer <JWT>
Idempotency-Key: <uuid>

Body:
{
  "user_id": "uuid",
  "amount": 500,
  "currency": "INR"
}

Behavior:
- API responds immediately
- Payment stored with status = PENDING
- Duplicate requests return original response
- Execution handled asynchronously by worker


====================================================
DEPLOYMENT STATUS
====================================================

Completed (Phase 1.1 + 1.2):
- Split Lambda images (API / Worker)
- Separate Dockerfiles for API and Worker
- Correct CMD per image
- API Lambda uses Mangum handler only
- Worker Lambda uses SQS handler only
- No async coroutine returned to Lambda runtime
- Terraform-managed AWS infrastructure
- End-to-end API → DB → EventBridge → SQS → Worker flow verified in AWS

Next Phase:
- Remove DB schema creation from startup
- Introduce Alembic migrations
- Harden IAM permissions
- Redis-backed idempotency
- DLQ monitoring and replay tooling


====================================================
DESIGN PRINCIPLES
====================================================

- Correctness over convenience
- Idempotency-first APIs
- Asynchronous execution for resilience
- Deterministic retries
- Failure isolation
- Cloud-native primitives
- Infrastructure defined as code


====================================================
AUTHOR NOTES
====================================================

This project is intentionally built in phases to mirror how real backend systems evolve in production. Each capability is added only after the previous layer is made correct, observable, and resilient. The emphasis is on system design, failure handling, and operational correctness rather than superficial feature count.
