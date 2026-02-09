resource "aws_ecr_repository" "lambda_repo" {
  name         = "${var.project_name}-lambda"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}
