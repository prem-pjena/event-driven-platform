########################################
# Global
########################################

variable "aws_region" {
  description = "AWS region to deploy infrastructure"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix used for all resources"
  type        = string
  default     = "event-platform"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

########################################
# Application
########################################

variable "secret_key" {
  description = "Application secret key"
  type        = string
  sensitive   = true
}

########################################
# Database
########################################

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

  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters long."
  }
}

########################################
# Lambda Image Tags
########################################

variable "api_image_tag" {
  description = "Docker image tag for API Lambda"
  type        = string
  default     = "api"
}

variable "worker_image_tag" {
  description = "Docker image tag for Payment Worker Lambda"
  type        = string
  default     = "worker"
}

variable "publisher_image_tag" {
  description = "Docker image tag for Outbox Publisher Lambda"
  type        = string
  default     = "publisher"
}

variable "dlq_image_tag" {
  description = "Docker image tag for DLQ Replay Lambda"
  type        = string
  default     = "dlq"
}

########################################
# Lambda Config
########################################

variable "lambda_memory_size" {
  description = "Default memory size for Lambda functions"
  type        = number
  default     = 1024
}

variable "lambda_timeout" {
  description = "Default timeout for Lambda functions"
  type        = number
  default     = 30
}



variable "alert_email" {
  description = "Email address for infrastructure alerts"
  type        = string
}
