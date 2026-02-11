########################################
# Database URL (ASYNC – Lambda)
########################################

resource "aws_secretsmanager_secret" "database_url" {
  name = "${var.project_name}/database-url"
}

resource "aws_secretsmanager_secret_version" "database_url_value" {
  secret_id = aws_secretsmanager_secret.database_url.id

  secret_string = jsonencode({
    url = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}?ssl=true"
  })
}

########################################
# Database URL (SYNC – Alembic / psycopg)
########################################

resource "aws_secretsmanager_secret" "database_url_sync" {
  name = "${var.project_name}/database-url-sync"
}

resource "aws_secretsmanager_secret_version" "database_url_sync_value" {
  secret_id = aws_secretsmanager_secret.database_url_sync.id

  secret_string = jsonencode({
    url = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}?sslmode=require"
  })
}

########################################
# Redis URL
########################################

resource "aws_secretsmanager_secret" "redis_url" {
  name = "${var.project_name}/redis-url"
}

resource "aws_secretsmanager_secret_version" "redis_url_value" {
  secret_id = aws_secretsmanager_secret.redis_url.id

  secret_string = jsonencode({
    url = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
  })
}
