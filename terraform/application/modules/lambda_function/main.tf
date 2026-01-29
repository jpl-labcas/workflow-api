locals {
  lambda_name = "labcas-${var.maturity}-workflows-${var.api_function_name}"
  source_file = "${path.cwd}/src/${var.api_function_name}/${var.api_function_name}.py"
  handler     = "${var.api_function_name}.lambda_handler"

}


resource "null_resource" "build_trigger" {
  triggers = {
    source_py_hash = filesha256(local.source_file)
  }
}

# Package the lambda source file as a zip

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = local.source_file
  output_path = "${path.module}/build/${local.lambda_name}.zip"
  depends_on  = [null_resource.build_trigger]
}

resource "aws_lambda_function" "this" {
  function_name    = local.lambda_name
  runtime          = var.runtime
  handler          = local.handler
  layers           = var.layers
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = var.lambda_role_arn
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = var.environment_variables
  }

  vpc_config {
    subnet_ids         = var.vpc_subnet_ids
    security_group_ids = var.vpc_security_group_ids
  }

  depends_on = [data.archive_file.lambda_zip]
}
