variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "event-platform"
}

variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "event_platform"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "event_user"
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}


