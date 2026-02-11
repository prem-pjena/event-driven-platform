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

  alarm_description = "DLQ has messages — payment processing failures"
  treat_missing_data = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_lambda_function" "dlq_replay" {
  function_name = "${var.project_name}-dlq-replay"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri = "${aws_ecr_repository.lambda_repo.repository_url}:dlq"


  timeout     = 60
  memory_size = 512

  environment {
    variables = {
      DLQ_URL        = aws_sqs_queue.payment_dlq.id
      EVENT_BUS_NAME = "default"
    }
  }
}


