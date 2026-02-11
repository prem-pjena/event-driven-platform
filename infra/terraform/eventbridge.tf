########################################
# EventBridge Bus
########################################
resource "aws_cloudwatch_event_bus" "payments_bus" {
  name = local.event_bus_name
}

########################################
# Payment Outcome Events
########################################
resource "aws_cloudwatch_event_rule" "payment_events" {
  name           = "${var.project_name}-payment-events"
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name

  # 🔥 FINAL EVENTS ONLY
  event_pattern = jsonencode({
    source = ["event-platform.payments"]
    "detail-type" = [
      "payment.success",
      "payment.failed"
    ]
  })
}
