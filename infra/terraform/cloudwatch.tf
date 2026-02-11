########################################
# DLQ Alarm
########################################
resource "aws_cloudwatch_metric_alarm" "payment_dlq_alarm" {
  alarm_name          = "${var.project_name}-payment-dlq-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0

  dimensions = {
    QueueName = aws_sqs_queue.payment_dlq.name
  }

  alarm_description   = "DLQ has messages — payment processing failures"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
}

########################################
# Outbox Publisher Schedule
########################################
resource "aws_cloudwatch_event_rule" "outbox_schedule" {
  name                = "${var.project_name}-outbox-schedule"
  schedule_expression = "rate(1 minute)"   # 🔥 5 seconds not allowed
}

resource "aws_cloudwatch_event_target" "outbox_target" {
  rule      = aws_cloudwatch_event_rule.outbox_schedule.name
  target_id = "outbox-publisher"
  arn       = aws_lambda_function.outbox_publisher.arn
}

resource "aws_lambda_permission" "allow_outbox_schedule" {
  statement_id  = "AllowOutboxScheduleInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.outbox_publisher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.outbox_schedule.arn
}

########################################
# DLQ Replay Schedule
########################################
resource "aws_cloudwatch_event_rule" "dlq_replay_schedule" {
  name                = "${var.project_name}-dlq-replay-schedule"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "dlq_replay_target" {
  rule      = aws_cloudwatch_event_rule.dlq_replay_schedule.name
  target_id = "dlq-replay"
  arn       = aws_lambda_function.dlq_replay.arn
}

resource "aws_lambda_permission" "allow_dlq_replay_schedule" {
  statement_id  = "AllowDLQReplayScheduleInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dlq_replay.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.dlq_replay_schedule.arn
}
