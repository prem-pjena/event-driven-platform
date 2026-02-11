########################################
# Dead Letter Queue
########################################
resource "aws_sqs_queue" "payment_dlq" {
  name                       = "${var.project_name}-payment-dlq"
  message_retention_seconds  = 1209600  # 14 days
  visibility_timeout_seconds = 60
}

########################################
# Main Payment Queue
########################################
resource "aws_sqs_queue" "payment_queue" {
  name                       = "${var.project_name}-payment-queue"
  visibility_timeout_seconds = 120
  message_retention_seconds  = 345600   # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.payment_dlq.arn
    maxReceiveCount     = 5
  })
}

########################################
# Allow EventBridge to send messages
########################################
resource "aws_sqs_queue_policy" "allow_eventbridge" {
  queue_url = aws_sqs_queue.payment_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEventBridgeSendMessage"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.payment_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_cloudwatch_event_rule.payment_events.arn
          }
        }
      }
    ]
  })
}
