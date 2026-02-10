resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"

  image_uri = "${aws_ecr_repository.lambda_repo.repository_url}:api"

  timeout     = 30
  memory_size = 1024

  # 🔥 THIS IS THE FIX 🔥
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
    DATABASE_URL = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}?ssl=disable"


    REDIS_URL = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
  }
}


  depends_on = [
  aws_iam_role_policy.lambda_eventbridge_publish,
  aws_iam_role_policy_attachment.lambda_vpc_access
]

}
