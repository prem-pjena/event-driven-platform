########################################
# ECR
########################################
output "ecr_repository_url" {
  description = "ECR repository for Lambda images"
  value       = aws_ecr_repository.lambda_repo.repository_url
}

########################################
# IAM
########################################
output "lambda_role_arn" {
  description = "IAM role assumed by Lambda functions"
  value       = aws_iam_role.lambda_role.arn
}

########################################
# Lambda Functions
########################################
output "api_lambda_name" {
  description = "API Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "payment_worker_lambda_name" {
  description = "Payment worker Lambda name"
  value       = aws_lambda_function.payment_worker.function_name
}

output "dlq_replay_lambda_name" {
  description = "DLQ replay Lambda name"
  value       = aws_lambda_function.dlq_replay.function_name
}

output "outbox_publisher_lambda_name" {
  description = "Outbox publisher Lambda name"
  value       = aws_lambda_function.outbox_publisher.function_name
}

########################################
# API Gateway
########################################
output "api_base_url" {
  description = "API Gateway base URL"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

########################################
# EventBridge
########################################
output "event_bus_name" {
  description = "EventBridge bus name"
  value       = aws_cloudwatch_event_bus.payments_bus.name
}

########################################
# Messaging (SQS)
########################################
output "payment_queue_url" {
  description = "SQS queue URL for payment events"
  value       = aws_sqs_queue.payment_queue.url
}

output "payment_queue_arn" {
  description = "SQS queue ARN"
  value       = aws_sqs_queue.payment_queue.arn
}

output "payment_dlq_url" {
  description = "Payment DLQ URL"
  value       = aws_sqs_queue.payment_dlq.url
}

########################################
# Bastion (Ops / Alembic)
########################################
output "bastion_public_ip" {
  description = "Public IP of bastion host (for SSH + Alembic)"
  value       = aws_instance.bastion.public_ip
}
