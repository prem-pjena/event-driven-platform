# Event-Driven Transaction & Notification Platform

A backend system inspired by **Razorpay / Amazon-style event-driven architectures**, focused on reliability, idempotency, and asynchronous processing.

This platform demonstrates **production-grade backend engineering practices** such as event-driven design, idempotent APIs, and scalable system architecture.

---

## 🏗️ Architecture

### Current Implementation
Client  
→ FastAPI (Async API)  
→ PostgreSQL  
→ Event Publisher (abstracted)

### Target Architecture
Client  
→ API Gateway  
→ FastAPI (AWS Lambda)  
→ EventBridge  
→ SQS  
→ Worker Lambdas  
→ External APIs (Payment / Email / SMS)

---

## 🔑 Key Capabilities

- Asynchronous, non-blocking API design
- Idempotent payment processing
- Event-driven system architecture
- Loose coupling between API and processing layers
- Designed for retries, DLQs, and failure recovery

---

## ⚙️ Tech Stack

### Backend
- FastAPI (async)
- Pydantic
- SQLAlchemy (async)

### Data Layer
- PostgreSQL

### Architecture & Reliability
- Event-driven design
- Idempotency via API + database constraints

### DevOps
- Docker & docker-compose
- Environment-based configuration

### Planned Enhancements
- AWS Lambda
- EventBridge
- SQS + Dead Letter Queue (DLQ)
- Redis (rate limiting & caching)
- Terraform (Infrastructure as Code)
- CI/CD with GitHub Actions

---

## 📦 API Example

### Create Payment
POST /payments  
Headers:  
Idempotency-Key: `<uuid>`

Body:
{
  "user_id": "uuid",
  "amount": 1000,
  "currency": "INR"
}

Behavior:
- Payment requests are processed asynchronously
- Duplicate requests with the same Idempotency-Key return the original response
- Database guarantees prevent duplicate payment records

---

## 🧪 Local Development

Start PostgreSQL:
docker compose up -d

Run the API:
uvicorn app.main:app --reload

API Documentation:
http://127.0.0.1:8000/docs

---

## 🧠 Design Decisions

- **Idempotency-first design** ensures safe retries and prevents double charging
- **Event abstraction** allows seamless migration to EventBridge and SQS
- **Async APIs** keep client latency low under load
- **Database constraints** act as the final guardrail for correctness

---

## 🚀 Roadmap
- Integrate AWS EventBridge for event routing
- Introduce SQS-based worker services
- Implement retry strategies and DLQs
- Build notification pipeline (Email/SMS)
- Add authentication, rate limiting, and observability

---

## 👨‍💻 Author Notes
This project is designed to reflect real-world backend systems used in high-scale fintech and e-commerce platforms, with a strong focus on correctness, reliability, and scalability.
