resource "aws_cloudwatch_event_bus" "payments_bus" {
  name = local.event_bus_name
}

resource "aws_cloudwatch_event_rule" "payment_events" {
  name           = "${var.project_name}-payment-events"
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name

  # 🔥 IMPORTANT:
  # Only FINAL outcome events are routed to SQS worker
  # payment.created.v1 MUST NOT be here
  event_pattern = jsonencode({
    source = ["event-platform.payments"]
    "detail-type" = [
      "payment.success",
      "payment.failed"
    ]
  })
}
