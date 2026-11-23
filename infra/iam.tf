data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  # Part C puts every secret in SSM Parameter Store under /agrivibe/<NAME>.
  ssm_prefix = "arn:aws:ssm:${var.region}:${local.account_id}:parameter/${var.name}"
}

# 1. Execution role: ECS (not your code) uses it to pull images, write logs and read secrets.
resource "aws_iam_role" "execution" {
  name = "${var.name}-ecs-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
      # Only ECS acting for THIS account may use the role (confused-deputy protection).
      Condition = { StringEquals = { "aws:SourceAccount" = local.account_id } }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  name = "read-agrivibe-secrets"
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameters"]
      Resource = "${local.ssm_prefix}/*"
    }]
  })
}

# 2. GitHub OIDC: GitHub Actions signs in with a short-lived token instead of stored keys.
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "deploy" {
  name = "${var.name}-github-deploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          # Only jobs in the "course" environment of these three repos.
          "token.actions.githubusercontent.com:sub" = [
            for repo in var.github_repos : "repo:${var.github_owner}/${repo}:environment:course"
          ]
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "deploy" {
  name = "push-images-and-roll-the-service"
  role = aws_iam_role.deploy.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "EcrLogin"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "EcrPush"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer",
        ]
        Resource = [for repo in aws_ecr_repository.app : repo.arn]
      },
      {
        Sid      = "TaskDefinitions"
        Effect   = "Allow"
        Action   = ["ecs:DescribeTaskDefinition", "ecs:RegisterTaskDefinition"]
        Resource = "*"
      },
      {
        Sid      = "RollTheService"
        Effect   = "Allow"
        Action   = ["ecs:UpdateService", "ecs:DescribeServices"]
        Resource = aws_ecs_service.app.id
      },
      {
        Sid       = "HandTheExecutionRoleToEcs"
        Effect    = "Allow"
        Action    = ["iam:PassRole"]
        Resource  = aws_iam_role.execution.arn
        Condition = { StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" } }
      },
    ]
  })
}