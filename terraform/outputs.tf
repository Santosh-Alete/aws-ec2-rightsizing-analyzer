output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.analyzer.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "s3_bucket_name" {
  description = "S3 bucket for reports"
  value       = aws_s3_bucket.reports.id
}

output "task_role_arn" {
  description = "ECS task role ARN"
  value       = aws_iam_role.ecs_task_role.arn
}

output "cross_account_role_name" {
  description = "Cross-account role name to deploy in target accounts"
  value       = aws_iam_role.cross_account_role.name
}
