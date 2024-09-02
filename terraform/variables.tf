variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "ecr_repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "ec2-rightsizing-analyzer"
}

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "ec2-rightsizing-cluster"
}

variable "ecs_task_cpu" {
  description = "ECS task CPU units"
  type        = string
  default     = "256"  # 0.25 vCPU
}

variable "ecs_task_memory" {
  description = "ECS task memory (MB)"
  type        = string
  default     = "512"  # 0.5 GB
}

variable "schedule_expression" {
  description = "EventBridge schedule expression"
  type        = string
  default     = "cron(0 8 * * ? *)"  # Daily at 8 AM UTC
}

variable "s3_bucket_name" {
  description = "S3 bucket for reports"
  type        = string
  default     = "ec2-rightsizing-reports"
}

variable "vpc_id" {
  description = "VPC ID for ECS tasks"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for ECS tasks"
  type        = list(string)
}
