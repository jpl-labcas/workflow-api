locals {
  lambda_name = "labcas-${var.maturity}-workflows-${api_function_name}"
  source_file = "${path.cwd}/src/${api_function_name}/${api_function_name}.py"
  handler     = "${api_function_name}.lambda_handler"

}


resource "null_resource" "build_trigger" {
  triggers = {
    source_py_hash = filesha256(var.source_file)
  }
}

# Package the lambda source file as a zip

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = var.source_file
  output_path = "${path.module}/build/${var.lambda_name}.zip"
  depends_on  = [null_resource.build_trigger]
}

resource "aws_lambda_function" "this" {
  function_name    = var.lambda_name
  runtime          = var.runtime
  handler          = var.handler
  layers           = var.layers
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = var.lambda_role_arn
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = var.environment_variables
  }
  depends_on = [data.archive_file.lambda_zip]
}

