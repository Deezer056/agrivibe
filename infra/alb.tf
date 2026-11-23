resource "aws_lb" "main" {
  name               = var.name
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  # Agent turns can take a while; the default 60 s would cut long answers off.
  idle_timeout = 300
}

# target_type "ip": Fargate tasks register by their own IP address, not by an EC2 instance.
resource "aws_lb_target_group" "frontend" {
  name                 = "${var.name}-frontend"
  port                 = 7860
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = aws_vpc.main.id
  deregistration_delay = 30

  health_check {
    path    = "/"
    matcher = "200"
  }
}

resource "aws_lb_target_group" "backend" {
  name                 = "${var.name}-backend"
  port                 = 8000
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = aws_vpc.main.id
  deregistration_delay = 30

  health_check {
    path    = "/health"
    matcher = "200"
  }
}

# Everything goes to the frontend unless a rule below says otherwise.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# Only the read-only backend pages are public. /chat and /knowledge stay private:
# the frontend reaches the backend over localhost inside the task.
resource "aws_lb_listener_rule" "backend" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/health", "/docs", "/openapi.json"]
    }
  }
}