########################################
# Identity (required for bus policy)
########################################
data "aws_caller_identity" "current" {}

########################################
# EventBridge Custom Bus
########################################
resource "aws_cloudwatch_event_bus" "payments_bus" {
  name = local.event_bus_name
}

########################################
# Allow this account to PutEvents
########################################
resource "aws_cloudwatch_event_bus_policy" "allow_account_put_events" {
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowAccountPutEvents"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "events:PutEvents"
        Resource = aws_cloudwatch_event_bus.payments_bus.arn
      }
    ]
  })
}

########################################
# Payment Events Rule
########################################
resource "aws_cloudwatch_event_rule" "payment_events" {
  name           = "${var.project_name}-payment-events"
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name

  event_pattern = jsonencode({
    source = ["event-platform.payments"],
    "detail-type" = [
      "payment.created",
      "payment.success",
      "payment.failed"
    ]
  })

  depends_on = [
    aws_cloudwatch_event_bus_policy.allow_account_put_events
  ]
}

########################################
# Target → SQS Queue
########################################
resource "aws_cloudwatch_event_target" "payment_to_sqs" {
  rule           = aws_cloudwatch_event_rule.payment_events.name
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name
  arn            = aws_sqs_queue.payment_queue.arn
  target_id      = "payment-to-sqs"

  depends_on = [
    aws_sqs_queue_policy.allow_eventbridge
  ]
}
