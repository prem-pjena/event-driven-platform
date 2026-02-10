########################################
# Secrets Manager – Database URLs
########################################

# ASYNC (used by Lambda workers / FastAPI async)
resource "aws_secretsmanager_secret" "database_url" {
  name = "${var.project_name}/database-url"
}

resource "aws_secretsmanager_secret_version" "database_url_value" {
  secret_id = aws_secretsmanager_secret.database_url.id

  # 🔥 asyncpg REQUIRES ssl=true
  secret_string = jsonencode({
    DATABASE_URL = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}?ssl=true"
  })
}


# SYNC (used by migrations / scripts / psycopg)
resource "aws_secretsmanager_secret" "database_url_sync" {
  name = "${var.project_name}/database-url-sync"
}

resource "aws_secretsmanager_secret_version" "database_url_sync_value" {
  secret_id = aws_secretsmanager_secret.database_url_sync.id

  secret_string = jsonencode({
    DATABASE_URL_SYNC = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/${var.db_name}?sslmode=require"
  })
}

########################################
# Redis Endpoint Secret
########################################

resource "aws_secretsmanager_secret" "redis_url" {
  name = "${var.project_name}/redis-url"
}

resource "aws_secretsmanager_secret_version" "redis_url_version" {
  secret_id = aws_secretsmanager_secret.redis_url.id
  secret_string = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379"
}
