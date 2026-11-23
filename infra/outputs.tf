output "app_url" {
  description = "Open this in a browser once the service is healthy."
  value       = "http://${aws_lb.main.dns_name}"
}

output "deploy_role_arn" {
  description = "GitHub variable AWS_ROLE_ARN in each repo (Step 10d)."
  value       = aws_iam_role.deploy.arn
}

output "ecr_repositories" {
  description = "Where Part C pushes the bootstrap images."
  value       = { for app, repo in aws_ecr_repository.app : app => repo.repository_url }
}

output "region" {
  description = "GitHub variable AWS_REGION in each repo (Step 10d)."
  value       = var.region
}