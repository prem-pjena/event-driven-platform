output "ecr_repository_url" {
  value = aws_ecr_repository.lambda_repo.repository_url
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}

output "api_lambda_name" {
  value = aws_lambda_function.api.function_name
}

output "api_base_url" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}

output "payment_queue_url" {
  value = aws_sqs_queue.payment_queue.url
}
