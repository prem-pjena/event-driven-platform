# --------------------------------------------------
# Lambda batch processor
# --------------------------------------------------
async def run_worker(event):
    records = event.get("Records", [])

    for record in records:
        try:
            body = json.loads(record["body"])
            detail = body.get("detail", {})
            raw_payment_id = detail.get("payment_id")

            if not raw_payment_id:
                logger.warning("MISSING_PAYMENT_ID")
                continue

            # 🔥 UUID VALIDATION (CRITICAL FIX)
            try:
                payment_uuid = uuid.UUID(str(raw_payment_id))
            except ValueError:
                logger.warning(
                    "INVALID_PAYMENT_ID_FORMAT",
                    extra={"payment_id": raw_payment_id},
                )
                continue

            await process_payment(str(payment_uuid))

        except Exception as exc:
            logger.exception(
                "WORKER_RECORD_FAILED",
                extra={"error": str(exc)},
            )
