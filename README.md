# Event-Driven Transaction & Notification Platform

## Architecture
Client → API Gateway → FastAPI (Lambda) → EventBridge → SQS → Worker Lambdas → External APIs

## Core Concepts
- Async event-driven processing
- Idempotency for payments
- Retry & DLQ handling
- Scalable serverless architecture

## Tech Stack
FastAPI, AWS Lambda, EventBridge, SQS, PostgreSQL, Redis, Terraform
