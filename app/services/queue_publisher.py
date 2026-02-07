import boto3
import json
import os

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["PAYMENT_QUEUE_URL"]

async def enqueue_payment(payment):
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({
            "payment_id": str(payment.id)
        }),
    )
