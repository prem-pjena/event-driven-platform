from locust import HttpUser, task, between
import uuid

class PaymentUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_payment(self):
        self.client.post(
            "/payments/",
            headers={
                "Authorization": "Bearer dummy",
                "Idempotency-Key": str(uuid.uuid4())
            },
            json={
                "user_id": "00000000-0000-0000-0000-000000000001",
                "amount": 500,
                "currency": "INR"
            }
        )
