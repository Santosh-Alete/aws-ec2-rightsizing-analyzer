# EventBridge Rule for Scheduled Execution
resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "ec2-rightsizing-schedule"
  description         = "Trigger EC2 rightsizing analysis daily"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "ecs_task" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "ec2-rightsizing-ecs-task"
  arn       = aws_ecs_cluster.main.arn
  role_arn  = aws_iam_role.eventbridge_role.arn
  
  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.analyzer.arn
    launch_type         = "FARGATE"
    
    network_configuration {
      subnets          = var.subnet_ids
      security_groups  = [aws_security_group.ecs_tasks.id]
      assign_public_ip = true
    }
  }
}
