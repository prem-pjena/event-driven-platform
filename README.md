# Event-Driven Transaction & Notification Platform

A production-grade backend system inspired by Razorpay- and Amazon-style event-driven architectures, built to demonstrate correctness-first backend engineering, asynchronous execution, idempotency, and cloud-native design using AWS-managed primitives.

The system is intentionally designed so that client-facing APIs remain fast, deterministic, and retry-safe, while all execution side effects (payments, notifications, analytics) are handled asynchronously and independently via background workers.

This repository reflects a real-world, incremental build of a distributed backend system. Each component was added only after the previous layer was made correct, observable, and failure-safe.


====================================================
SYSTEM ARCHITECTURE (CURRENT – IMPLEMENTED & VERIFIED)
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
Amazon EventBridge (Custom Bus)
  |
  |  Fan-out
  v
Amazon SQS Queue
  |
  |  Event Source Mapping
  v
Worker Lambda
  |
  |  External Calls
  v
Payment Gateway / Notifications


Key Property:
Client latency is fully isolated from payment execution and all downstream side effects.


====================================================
SEQUENCE — PAYMENT CREATION (SYNCHRONOUS PATH)
====================================================

Client           API Lambda            PostgreSQL
  |                  |                     |
  | POST /payments   |                     |
  |----------------->|                     |
  |                  | Validate request    |
  |                  | Require idempotency |
  |                  | Insert payment      |
  |                  | status = PENDING    |
  |                  |-------------------->|
  |                  |                     |
  | 201 Created      |                     |
  |<-----------------|                     |


Properties:
- No external calls in API execution path
- Deterministic behavior
- Retry-safe via Idempotency-Key + DB constraints
- API Lambda uses Mangum handler only (Lambda-safe)
- API returns immediately after persistence


====================================================
SEQUENCE — ASYNCHRONOUS EXECUTION (WORKER PATH)
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
- Effectively-once processing via payment state checks
- Terminal state committed before emitting outcome events
- Worker Lambda is triggered only by SQS (no HTTP)


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
- Retries are bounded and deterministic
- Poison messages handled via DLQ


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
CORE CAPABILITIES (IMPLEMENTED & VERIFIED)
====================================================

- Asynchronous, non-blocking API design using FastAPI
- Idempotent payment creation enforced via Idempotency-Key + DB constraints
- Strict separation between API intent handling and execution logic
- Background payment processing using SQS-triggered worker Lambda
- Retry-safe worker execution with terminal state persistence
- Event-driven architecture using EventBridge + SQS fan-out
- Effectively-once semantics built on top of at-least-once delivery
- Failure isolation between API, workers, and downstream consumers
- Infrastructure as Code using Terraform
- Fully containerized Lambdas using separate Docker images
- Clean Lambda handler separation (API vs Worker)
- Lambda-safe async execution (single event loop per invocation)
- Async SQLAlchemy usage without cross-loop contamination
- Explicit engine lifecycle management per worker invocation
- Schema-tolerant EventBridge → SQS consumer design
- End-to-end event flow verified in real AWS (no mocks)


====================================================
CURRENT SYSTEM BEHAVIOR (END-TO-END VERIFIED)
====================================================

- Clients call POST /payments
- API Lambda:
  - Uses Mangum handler only
  - Validates request
  - Requires Idempotency-Key
  - Persists payment with status = PENDING
  - Returns response immediately (HTTP 201)
- Duplicate requests return the original persisted payment
- API Lambda does NOT execute payments or publish outcome events
- Domain events are emitted asynchronously
- EventBridge successfully routes events
- Events are delivered to SQS and consumed by worker Lambda
- Worker Lambda:
  - Triggered only by SQS
  - Consumes EventBridge-shaped messages
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
- Terraform (Infrastructure as Code)

Observability:
- Structured logging
- Correlation IDs
- CloudWatch Logs


====================================================
API EXAMPLE
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
PROJECT STRUCTURE
====================================================

tree
.
├── alembic
│   ├── env.py
│   ├── versions
│   └── script.py.mako
├── app
│   ├── api
│   │   └── routes
│   │       ├── payments.py
│   │       └── notifications.py
│   ├── core
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── events
│   │   └── payment_events.py
│   ├── services
│   │   ├── event_publisher.py
│   │   ├── fake_gateway.py
│   │   └── payment_service.py
│   ├── shared
│   │   ├── models.py
│   │   └── schemas.py
│   └── workers
│       ├── payment_worker.py
│       ├── sqs_worker.py
│       └── db
│           └── session.py
├── infra
│   └── terraform
│       ├── apigateway.tf
│       ├── eventbridge.tf
│       ├── sqs.tf
│       ├── lambda_api.tf
│       ├── lambda_worker.tf
│       ├── iam.tf
│       └── rds.tf
├── Dockerfile.api
├── Dockerfile.worker
├── docker-compose.yml
├── requirements
│   ├── prod.txt
│   ├── dev.txt
│   └── migrations.txt
├── locustfile.py
└── README.md


====================================================
DEPLOYMENT STATUS
====================================================

Completed:
- Split Lambda images (API / Worker)
- Separate Dockerfiles per Lambda
- Correct CMD per image
- API Lambda uses Mangum handler only
- Worker Lambda uses SQS handler only
- Async SQLAlchemy usage is Lambda-safe
- EventBridge → SQS → Worker flow verified
- Payment retries validated under failure scenarios
- End-to-end execution verified in AWS

Planned (Next Phase):
- Alembic-based schema migrations
- Redis-backed idempotency
- Hardened IAM permissions
- DLQ monitoring and replay tooling
- Additional downstream consumers (notifications, analytics)


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
