variable "aws_profile" {
  description = "AWS CLI profile to use for authentication"
  type        = string
}

variable "aws_region" {
  description = "AWS region for logs and account-specific settings"
  type        = string
}

variable "maturity" {
  description = "Maturity level of the deployment (poc: aws console exploration, iac: terraform deployment, ops: full automation with CICD or SA documented procedures)"
  type        = string
}

variable "lambda_role_arn" {
  description = "IAM role that the lanbda function assumes"
  type        = string
}

variable "stage" {
  description = "Name of the deployment stage (e.g., dev, staging, prod)"
  type        = string
}

variable "s3_bucket_staging" {
    description = "S3 bucket for staging"
    type        = string
}

variable "mwaa_env_name" {
    description = "MWAA environment name"
    type        = string
}

variable "jwt_secret_arn" {
    description = "ARN of the JWT secret in AWS Secrets Manager"
    type        = string
}

variable "vpc_subnet_ids" {
  description = "List of subnet IDs for Lambda VPC config."
  type        = list(string)
  default     = []
}

variable "vpc_security_group_ids" {
  description = "List of security group IDs for Lambda VPC config."
  type        = list(string)
  default     = []
}



