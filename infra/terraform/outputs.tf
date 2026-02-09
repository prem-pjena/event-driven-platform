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
# API Lambda
########################################
output "api_lambda_name" {
  description = "API Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "api_base_url" {
  description = "API Gateway base URL"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

########################################
# Messaging
########################################
output "payment_queue_url" {
  description = "SQS queue URL for payment events"
  value       = aws_sqs_queue.payment_queue.url
}

########################################
# Bastion (Ops / Alembic)
########################################
output "bastion_public_ip" {
  description = "Public IP of bastion host (for SSH + Alembic)"
  value       = aws_instance.bastion.public_ip
}
