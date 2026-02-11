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
      # 🔥 EXACTLY what asyncpg expects
      DATABASE_URL = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}?ssl=disable"


      REDIS_URL = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.payment_queue.arn
  function_name    = aws_lambda_function.payment_worker.arn
  batch_size       = 1
}
