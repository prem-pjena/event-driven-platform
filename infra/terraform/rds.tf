
resource "aws_db_subnet_group" "db_subnet_group" {
  name       = "${var.project_name}-db-subnets"
  subnet_ids = [aws_subnet.subnet_a.id, aws_subnet.subnet_b.id]
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-db"

  engine         = "postgres"
  engine_version = "15.14"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  db_name           = var.db_name
  username          = var.db_username
  password          = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.lambda_db_sg.id]

  publicly_accessible = false
  skip_final_snapshot = true
}