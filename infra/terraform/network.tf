########################################
# VPC
########################################
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "event-platform-vpc"
  }
}

########################################
# Subnets
########################################
resource "aws_subnet" "subnet_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "event-platform-subnet-a"
  }
}

resource "aws_subnet" "subnet_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "event-platform-subnet-b"
  }
}

########################################
# Security Group: Lambda + RDS + VPC Endpoints
########################################
resource "aws_security_group" "lambda_db_sg" {
  name   = "event-platform-lambda-db-sg"
  vpc_id = aws_vpc.main.id

  # PostgreSQL (RDS)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # Allow PostgreSQL from Bastion (EC2 migrations)
ingress {
  from_port       = 5432
  to_port         = 5432
  protocol        = "tcp"
  security_groups = [aws_security_group.bastion_sg.id]
}


  # 🔥 REQUIRED: HTTPS inside VPC (VPC Endpoints)
  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "event-platform-lambda-db-sg"
  }
}

########################################
# Security Group: Bastion
########################################
resource "aws_security_group" "bastion_sg" {
  name   = "event-platform-bastion-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["119.252.204.202/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

########################################
# Redis Subnet Group
########################################
resource "aws_elasticache_subnet_group" "redis_subnets" {
  name       = "${var.project_name}-redis-subnets"
  subnet_ids = [
    aws_subnet.subnet_a.id,
    aws_subnet.subnet_b.id
  ]
}

########################################
# Redis Security Group
########################################
resource "aws_security_group" "redis_sg" {
  name   = "${var.project_name}-redis-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda_db_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

########################################
# VPC Interface Endpoints (REQUIRED)
########################################

# EventBridge
resource "aws_vpc_endpoint" "eventbridge" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.us-east-1.events"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
  security_group_ids  = [aws_security_group.lambda_db_sg.id]
  private_dns_enabled = true
}

# SQS
resource "aws_vpc_endpoint" "sqs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.us-east-1.sqs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
  security_group_ids  = [aws_security_group.lambda_db_sg.id]
  private_dns_enabled = true
}

# 🔥 Secrets Manager (CRITICAL)
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.us-east-1.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
  security_group_ids  = [aws_security_group.lambda_db_sg.id]
  private_dns_enabled = true
}

# 🔥 CloudWatch Logs (CRITICAL)
resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.us-east-1.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
  security_group_ids  = [aws_security_group.lambda_db_sg.id]
  private_dns_enabled = true
}

# STS
resource "aws_vpc_endpoint" "sts" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.us-east-1.sts"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
  security_group_ids  = [aws_security_group.lambda_db_sg.id]
  private_dns_enabled = true
}

# EC2 Messages (Lambda runtime)
resource "aws_vpc_endpoint" "ec2messages" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.us-east-1.ec2messages"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
  security_group_ids  = [aws_security_group.lambda_db_sg.id]
  private_dns_enabled = true
}
