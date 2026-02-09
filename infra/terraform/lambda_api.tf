resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"

  image_uri = "${aws_ecr_repository.lambda_repo.repository_url}:api"

  timeout     = 30
  memory_size = 1024

  environment {
    variables = {
      USE_AWS_EVENTS = "true"
      EVENT_BUS_NAME = aws_cloudwatch_event_bus.payments_bus.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_eventbridge_policy
  ]
}
