terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # The state file lives in the S3 bucket from Part A, not on this device.
  backend "s3" {
    bucket       = "agrivibe-tfstate-195408553931"
    key          = "agrivibe/terraform.tfstate"
    region       = "ap-southeast-2"
    encrypt      = true
    use_lockfile = true # a lockfile in S3 stops two applies running at once
  }
}

provider "aws" {
  region = var.region

  # Every resource gets these tags, so the console and the bill show what belongs to agrivibe.
  default_tags {
    tags = {
      Project   = "agrivibe"
      ManagedBy = "terraform"
    }
  }
}
