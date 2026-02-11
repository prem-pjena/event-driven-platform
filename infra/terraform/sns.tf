########################################
# SNS Topic – System Alerts
########################################

resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"
}

########################################
# Email Subscription
########################################

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
