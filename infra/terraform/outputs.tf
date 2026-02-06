output "payment_queue_url" {
  value = aws_sqs_queue.payment_queue.id
}
