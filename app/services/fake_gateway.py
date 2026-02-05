import random
import asyncio

class PaymentGatewayError(Exception):
    pass

async def charge(amount: int):
    await asyncio.sleep(1)  # simulate network delay

    # 70% success, 30% failure
    if random.random() < 0.3:
        raise PaymentGatewayError("Gateway timeout")

    return {"status": "SUCCESS"}
