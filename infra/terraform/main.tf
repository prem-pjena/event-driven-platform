provider "aws" {
  region = "us-east-1"
}

resource "aws_sqs_queue" "payment_queue" {
  name = "payment-queue"
}

resource "aws_sqs_queue" "payment_dlq" {
  name = "payment-dlq"
}

resource "aws_sqs_queue_redrive_policy" "payment_redrive" {
  queue_url = aws_sqs_queue.payment_queue.id

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.payment_dlq.arn
    maxReceiveCount     = 5
  })
}
