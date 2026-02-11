########################################
# EventBridge Bus
########################################
resource "aws_cloudwatch_event_bus" "payments_bus" {
  name = local.event_bus_name
}

########################################
# Payment Events Rule
########################################
resource "aws_cloudwatch_event_rule" "payment_events" {
  name           = "${var.project_name}-payment-events"
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name

  # Match ALL events from publisher
  event_pattern = jsonencode({
    source = ["event-platform.payments"]
  })
}

########################################
# Target → SQS Queue
########################################
resource "aws_cloudwatch_event_target" "payment_to_sqs" {
  rule           = aws_cloudwatch_event_rule.payment_events.name
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name
  arn            = aws_sqs_queue.payment_queue.arn

  depends_on = [
    aws_sqs_queue_policy.allow_eventbridge
  ]
}

