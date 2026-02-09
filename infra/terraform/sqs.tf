########################################
# SQS Queues
########################################
resource "aws_sqs_queue" "payment_dlq" {
  name = "${var.project_name}-payment-dlq"
}

resource "aws_sqs_queue" "payment_queue" {
  name                       = "${var.project_name}-payment-queue"
  visibility_timeout_seconds = 120

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.payment_dlq.arn
    maxReceiveCount     = 5
  })
}

########################################
# EventBridge → SQS Target (FIXED)
########################################
resource "aws_cloudwatch_event_target" "payment_to_sqs" {
  rule           = aws_cloudwatch_event_rule.payment_events.name
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name
  arn            = aws_sqs_queue.payment_queue.arn

  input_transformer {
    input_paths = {
      payment_id = "$.detail.payment_id"
    }

    input_template = <<EOF
{
  "payment_id": <payment_id>
}
EOF
  }
}


########################################
# 🔥 REQUIRED: Allow EventBridge to send to SQS
########################################
resource "aws_sqs_queue_policy" "allow_eventbridge" {
  queue_url = aws_sqs_queue.payment_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
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
