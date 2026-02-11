resource "aws_lambda_function" "outbox_publisher" {
  function_name = "${var.project_name}-outbox-publisher"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"

  image_uri = "${aws_ecr_repository.lambda_repo.repository_url}:publisher"

  timeout     = 30
  memory_size = 1024

  # 🔥 DO NOT define handler
  # 🔥 DO NOT define runtime

  vpc_config {
    subnet_ids = [
      aws_subnet.subnet_a.id,
      aws_subnet.subnet_b.id
    ]
    security_group_ids = [
      aws_security_group.lambda_db_sg.id
    ]
  }

  environment {
    variables = {
      DATABASE_URL = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}?ssl=true"
      EVENT_BUS_NAME = aws_cloudwatch_event_bus.payments_bus.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_eventbridge_publish,
    aws_iam_role_policy_attachment.lambda_vpc_access
  ]
}

resource "aws_lambda_permission" "allow_eventbridge_outbox" {
  statement_id  = "AllowExecutionFromEventBridgeOutbox"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.outbox_publisher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.outbox_schedule.arn
}
