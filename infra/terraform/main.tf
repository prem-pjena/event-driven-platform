########################################
# Locals
########################################
locals {
  event_bus_name = "payments-bus"
}

########################################
# ECR Repository
########################################
resource "aws_ecr_repository" "lambda_repo" {
  name         = "${var.project_name}-lambda"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

########################################
# IAM Role for Lambda
########################################
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

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

########################################
# EventBridge Permissions (SCOPED)
########################################
resource "aws_iam_role_policy" "lambda_eventbridge_policy" {
  name = "${var.project_name}-lambda-eventbridge"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["events:PutEvents"]
      Resource = aws_cloudwatch_event_bus.payments_bus.arn
    }]
  })
}

########################################
# VPC
########################################
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
}

resource "aws_subnet" "subnet_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "subnet_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}

########################################
# Security Group (Lambda + RDS)
########################################
resource "aws_security_group" "lambda_db_sg" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

########################################
# RDS
########################################
resource "aws_db_subnet_group" "db_subnet_group" {
  name       = "${var.project_name}-db-subnets"
  subnet_ids = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-db"

  engine         = "postgres"
  engine_version = "15.14"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  db_name           = var.db_name
  username          = var.db_username
  password          = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.lambda_db_sg.id]

  publicly_accessible = false
  skip_final_snapshot = true
}

########################################
# Secrets Manager
########################################
resource "aws_secretsmanager_secret" "database_url" {
  name = "${var.project_name}/database-url"
}

resource "aws_secretsmanager_secret_version" "database_url_version" {
  secret_id = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
}

########################################
# EventBridge Bus (CRITICAL)
########################################
resource "aws_cloudwatch_event_bus" "payments_bus" {
  name = local.event_bus_name
}

########################################
# API Lambda
########################################
resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_repo.repository_url}:api"

  timeout     = 30
  memory_size = 1024

  vpc_config {
    subnet_ids         = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
    security_group_ids = [aws_security_group.lambda_db_sg.id]
  }

  environment {
    variables = {
      DATABASE_URL   = aws_secretsmanager_secret_version.database_url_version.secret_string
      USE_AWS_EVENTS = "true"
      EVENT_BUS_NAME = aws_cloudwatch_event_bus.payments_bus.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_eventbridge_policy
  ]
}

########################################
# API Gateway (HTTP API v2)
########################################
resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.project_name}-http-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.api.invoke_arn
}

resource "aws_apigatewayv2_route" "proxy_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "root_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

########################################
# SQS + DLQ
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
# CUSTOM SQS IAM POLICY (CORRECT)
########################################
resource "aws_iam_policy" "lambda_sqs_policy" {
  name = "event-platform-lambda-sqs-access"

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
      Resource = aws_sqs_queue.payment_queue.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_sqs_policy.arn
}

########################################
# EventBridge Rule
########################################
resource "aws_cloudwatch_event_rule" "payment_events" {
  name           = "${var.project_name}-payment-events"
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name

  event_pattern = jsonencode({
    source = ["event-platform.payments"]
    detail-type = [
      "payment.created.v1",
      "payment.success",
      "payment.failed"
    ]
  })
}

########################################
# EventBridge → SQS Target
########################################
resource "aws_cloudwatch_event_target" "payment_to_sqs" {
  rule           = aws_cloudwatch_event_rule.payment_events.name
  event_bus_name = aws_cloudwatch_event_bus.payments_bus.name
  arn            = aws_sqs_queue.payment_queue.arn
}

########################################
# Allow EventBridge → SQS
########################################
resource "aws_sqs_queue_policy" "allow_eventbridge" {
  queue_url = aws_sqs_queue.payment_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.payment_queue.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.payment_events.arn
        }
      }
    }]
  })
}

########################################
# Worker Lambda
########################################
resource "aws_lambda_function" "payment_worker" {
  function_name = "${var.project_name}-payment-worker"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_repo.repository_url}:worker"

  timeout     = 60
  memory_size = 1024

  vpc_config {
    subnet_ids         = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
    security_group_ids = [aws_security_group.lambda_db_sg.id]
  }

  environment {
    variables = {
      DATABASE_URL = aws_secretsmanager_secret_version.database_url_version.secret_string
    }
  }
}

########################################
# SQS → Lambda Trigger
########################################
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.payment_queue.arn
  function_name    = aws_lambda_function.payment_worker.arn
  batch_size       = 1

  depends_on = [
    aws_iam_role_policy_attachment.lambda_sqs_access
  ]
}
