data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/my_lambda"
  output_path = "${path.module}/build/my_lambda.zip"
}

resource "aws_lambda_function" "authorizer" {
  function_name = "labcas-workflows-authorizer"
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  role   = aws_iam_role.lambda_role.arn
  timeout = 30
  memory_size = 512

  environment {
    variables = {
      STAGE = var.stage
    }
  }
}
