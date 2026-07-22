def generate_terraform_assets(provider="AWS", region="us-east-1", environment="prod"):
    """Generate standardized enterprise-grade Terraform configurations."""
    provider_lower = provider.lower()
    
    if "aws" in provider_lower:
        return _generate_aws_tf(region, environment)
    elif "gcp" in provider_lower:
        return _generate_gcp_tf(region, environment)
    else:
        return _generate_aws_tf(region, environment)

def _generate_aws_tf(region, env):
    providers = f"""# Terraform AWS Provider Configuration
terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
  default_tags {{
    tags = {{
      Environment = var.environment
      Project     = "CICDPipelineDemo"
      ManagedBy   = "Terraform"
    }}
  }}
}}
"""

    variables = f"""variable "aws_region" {{
  description = "The target AWS region to deploy infrastructure"
  type        = string
  default     = "{region}"
}}

variable "environment" {{
  description = "Deployment environment namespace"
  type        = string
  default     = "{env}"
}}

variable "vpc_cidr" {{
  description = "CIDR block for the custom VPC"
  type        = string
  default     = "10.0.0.0/16"
}}

variable "instance_type" {{
  description = "EC2 instance size for target workloads"
  type        = string
  default     = "t3.medium"
}}
"""

    main = f"""# Custom VPC Config
resource "aws_vpc" "main" {{
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
}}

# Public Subnets
resource "aws_subnet" "public_1" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${{var.aws_region}}a"
  map_public_ip_on_launch = true
}}

resource "aws_subnet" "public_2" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${{var.aws_region}}b"
  map_public_ip_on_launch = true
}}

# Internet Gateway
resource "aws_internet_gateway" "gw" {{
  vpc_id = aws_vpc.main.id
}}

# Route Table
resource "aws_route_table" "public" {{
  vpc_id = aws_vpc.main.id
  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }}
}}

# Route Table Associations
resource "aws_route_table_association" "pub_1" {{
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}}

resource "aws_route_table_association" "pub_2" {{
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}}

# Application Security Group
resource "aws_security_group" "web_sg" {{
  name        = "${{var.environment}}-web-sg"
  description = "Allow port 80/443 inbound"
  vpc_id      = aws_vpc.main.id

  ingress {{
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  egress {{
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }}
}}

# Application Load Balancer
resource "aws_lb" "web_alb" {{
  name               = "${{var.environment}}-web-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.web_sg.id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}}
"""

    outputs = """output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "alb_dns" {
  description = "DNS name of the application load balancer"
  value       = aws_lb.web_alb.dns_name
}
"""

    return {
        "providers.tf": providers,
        "variables.tf": variables,
        "main.tf": main,
        "outputs.tf": outputs
    }

def _generate_gcp_tf(region, env):
    providers = """terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.gcp_region
}
"""

    variables = f"""variable "project_id" {{
  description = "The target GCP Project ID"
  type        = string
  default     = "my-gcp-project"
}}

variable "gcp_region" {{
  description = "Target GCP region"
  type        = string
  default     = "{region}"
}}

variable "environment" {{
  description = "Environment name"
  type        = string
  default     = "{env}"
}}
"""

    main = """# VPC network
resource "google_compute_network" "vpc" {
  name                    = "${var.environment}-vpc"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.environment}-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.gcp_region
  network       = google_compute_network.vpc.id
}

# Firewall rule
resource "google_compute_firewall" "allow_http" {
  name    = "${var.environment}-allow-http"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web-server"]
}
"""

    outputs = """output "network_name" {
  value = google_compute_network.vpc.name
}
"""

    return {
        "providers.tf": providers,
        "variables.tf": variables,
        "main.tf": main,
        "outputs.tf": outputs
    }
