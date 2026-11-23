locals {
  backend_secrets = [
    "OPENAI_API_KEY", "PINECONE_API_KEY", "DATABASE_URL",
    "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL",
    "PINECONE_INDEX", "FARMER_ID", "FARMER_NAME",
  ]
  image = { for app, repo in aws_ecr_repository.app : app => "${repo.repository_url}:${var.image_tag}" }
  log_options = {
    "awslogs-group"  = aws_cloudwatch_log_group.app.name
    "awslogs-region" = var.region
  }
}

resource "aws_ecs_cluster" "main" {
  name = var.name
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.name}"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "app" {
  family                   = var.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.execution.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name         = "fieldsat"
      image        = local.image["fieldsat"]
      essential    = true
      portMappings = [{ containerPort = 8001 }]
      healthCheck = {
        command     = ["CMD", "python", "-c", "import socket; socket.create_connection(('127.0.0.1', 8001), 2)"]
        interval    = 10
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }
      logConfiguration = { logDriver = "awslogs", options = merge(local.log_options, { "awslogs-stream-prefix" = "fieldsat" }) }
    },
    {
      name         = "backend"
      image        = local.image["backend"]
      essential    = true
      portMappings = [{ containerPort = 8000 }]
      dependsOn    = [{ containerName = "fieldsat", condition = "HEALTHY" }]
      environment = [
        { name = "LANGFUSE_ENVIRONMENT", value = "production" },
        { name = "MODERATION", value = "false" }, # the class OpenAI key gets 403 on Moderations
        { name = "FIELDSAT_URL", value = "http://127.0.0.1:8001/mcp" },
      ]
      secrets = [for n in local.backend_secrets : { name = n, valueFrom = "${local.ssm_prefix}/${n}" }]
      healthCheck = {
        command     = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
        interval    = 10
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
      logConfiguration = { logDriver = "awslogs", options = merge(local.log_options, { "awslogs-stream-prefix" = "backend" }) }
    },
    {
      name             = "frontend"
      image            = local.image["frontend"]
      essential        = true
      portMappings     = [{ containerPort = 7860 }]
      dependsOn        = [{ containerName = "backend", condition = "HEALTHY" }]
      environment      = [{ name = "AGRIVIBE_API", value = "http://127.0.0.1:8000" }]
      logConfiguration = { logDriver = "awslogs", options = merge(local.log_options, { "awslogs-stream-prefix" = "frontend" }) }
    },
  ])
}

resource "aws_ecs_service" "app" {
  name            = var.name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  # Give the three containers time to start before the ALB health checks count.
  health_check_grace_period_seconds = 180

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.task.id]
    assign_public_ip = true # to reach OpenAI, Neon, Pinecone and Langfuse without a NAT gateway
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 7860
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  # A deploy whose new task never turns healthy rolls back to the last good one.
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.http]

  lifecycle {
    # deploy.yml registers new task-definition revisions. Without this, the next
    # terraform apply would roll the service back to the "bootstrap" images.
    ignore_changes = [task_definition]
  }
}