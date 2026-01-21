variable "api_function_name"  {
  description = "Shortname of the API Lambda function."
  type        = string
}

variable "maturity" {
  description = "Maturity level of the deployment (poc: aws console exploration, iac: terraform deployment, ops: full automation with CICD or SA documented procedures)"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime."
  type        = string
  default     = "python3.13"
}



variable "layers" {
  description = "List of Lambda layer ARNs."
  type        = list(string)
  default     = []
}

variable "lambda_role_arn" {
  description = "IAM role ARN for Lambda."
  type        = string
}

variable "timeout" {
  description = "Lambda timeout."
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Lambda memory size."
  type        = number
  default     = 512
}

variable "environment_variables" {
  description = "Map of environment variables."
  type        = map(string)
  default     = {}
}

