########################################
# EventBridge Bus
########################################
resource "aws_cloudwatch_event_bus" "payments_bus" {
  name = local.event_bus_name
}

########################################
# Payment Outcome Rule
########################################
resource "aws_cloudwatch_event_rule" "payment_events" {
  name           = "${var.project_name}-payment-events"
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name

  event_pattern = jsonencode({
    source = ["event-platform.payments"]
    "detail-type" = [
      "payment.success",
      "payment.failed"
    ]
  })
}

########################################
# Target → Notification Lambda
########################################
resource "aws_cloudwatch_event_target" "payment_notifications_target" {
  rule           = aws_cloudwatch_event_rule.payment_events.name
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name
  arn            = aws_lambda_function.api.arn
}

########################################
# Allow EventBridge to invoke Lambda
########################################
resource "aws_lambda_permission" "allow_eventbridge_invoke_api" {
  statement_id  = "AllowEventBridgeInvokeAPI"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.payment_events.arn
}
