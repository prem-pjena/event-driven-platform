########################################
# Bastion EC2 (for Alembic / Ops)
########################################

resource "aws_key_pair" "bastion_key" {
  key_name   = "${var.project_name}-bastion-key"
  public_key = file("${path.module}/../keys/event-platform-bastion.pub")
}

resource "aws_instance" "bastion" {
  ami           = "ami-0c02fb55956c7d316" # Amazon Linux 2 (us-east-1)
  instance_type = "t3.micro"

  subnet_id = aws_subnet.subnet_a.id

  # 🔥 IMPORTANT: Bastion gets ITS OWN SG
  vpc_security_group_ids = [
    aws_security_group.bastion_sg.id
  ]

  key_name = aws_key_pair.bastion_key.key_name

  associate_public_ip_address = true

  tags = {
    Name = "${var.project_name}-bastion"
  }
}
