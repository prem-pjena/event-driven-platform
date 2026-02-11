resource "aws_lambda_function" "dlq_replay" {
  function_name = "${var.project_name}-dlq-replay"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"

  image_uri = "${aws_ecr_repository.lambda_repo.repository_url}:dlq"

  timeout     = 60
  memory_size = 512

  # 🔥 MUST be in VPC (same as other Lambdas)
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
      DLQ_URL            = aws_sqs_queue.payment_dlq.id
      MAIN_QUEUE_URL     = aws_sqs_queue.payment_queue.id
      EVENT_BUS_NAME     = "default"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_vpc_access
  ]
}

resource "aws_lambda_permission" "allow_eventbridge_dlq" {
  statement_id  = "AllowExecutionFromEventBridgeDLQ"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dlq_replay.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.dlq_replay_schedule.arn
}