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
# Security Group: Lambda + RDS
########################################
resource "aws_security_group" "lambda_db_sg" {
  name   = "event-platform-lambda-db-sg"
  vpc_id = aws_vpc.main.id

  # 🔐 PostgreSQL — internal VPC only
  ingress {
    description = "Postgres from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # 🌍 Outbound allowed
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
# Security Group: Bastion (SSH ONLY)
########################################
resource "aws_security_group" "bastion_sg" {
  name   = "event-platform-bastion-sg"
  vpc_id = aws_vpc.main.id

  # 🔑 SSH from your Mac ONLY
  ingress {
    description = "SSH from Prem Mac"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["119.252.204.202/32"]
  }

  # 🌍 Outbound allowed
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "event-platform-bastion-sg"
  }
}
