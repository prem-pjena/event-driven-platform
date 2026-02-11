# ==================================================
# Lambda Execution Role
# ==================================================
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# ==================================================
# Basic Logging (CloudWatch)
# ==================================================
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ==================================================
# VPC Networking (ENI access)
# ==================================================
resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# ==================================================
# EventBridge Publish (API + Publisher)
# ==================================================
resource "aws_iam_role_policy" "lambda_eventbridge_publish" {
  name = "${var.project_name}-lambda-eventbridge-publish"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["events:PutEvents"]
      Resource = aws_cloudwatch_event_bus.payments_bus.arn
    }]
  })
}

# ==================================================
# SQS Consumer (Worker)
# ==================================================
resource "aws_iam_role_policy" "lambda_sqs_consumer_policy" {
  name = "${var.project_name}-lambda-sqs-consumer"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ChangeMessageVisibility"
      ]
      Resource = [
        aws_sqs_queue.payment_queue.arn,
        aws_sqs_queue.payment_dlq.arn
      ]
    }]
  })
}

# ==================================================
# SQS Publisher (Outbox + DLQ Replay)
# ==================================================
resource "aws_iam_role_policy" "lambda_sqs_publish" {
  name = "${var.project_name}-lambda-sqs-publish"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["sqs:SendMessage"]
      Resource = aws_sqs_queue.payment_queue.arn
    }]
  })
}

########################################
# Lambda → Secrets Manager Access
########################################

resource "aws_iam_role_policy" "lambda_secrets_access" {
  name = "${var.project_name}-lambda-secrets-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.database_url.arn,
          aws_secretsmanager_secret.database_url_sync.arn,
          aws_secretsmanager_secret.redis_url.arn
        ]
      }
    ]
  })
}
