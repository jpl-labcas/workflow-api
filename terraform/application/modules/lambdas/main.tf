resource "null_resource" "prepare_layer" {
  provisioner "local-exec" {
    command = "mkdir -p ./build/layer/python && pip install -r requirements.txt -t ./build/layer/python"
  }
}

data "archive_file" "lambda_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build/layer"
  output_path = "${path.module}/build/layer.zip"
  depends_on  = [null_resource.prepare_layer]
}

data "archive_file" "lambda_authorizer_zip" {
  type        = "zip"
  source_file  = "${path.module}/src/authorizer.py"
  output_path = "${path.module}/build/authorizer.zip"
}

resource "aws_lambda_layer_version" "layer" {
  layer_name          = "labcas-${var.maturity}-workflows-layer"
  filename            = data.archive_file.lambda_layer_zip.output_path
  compatible_runtimes = ["python3.13"]
  description         = "Common dependencies for LabCAS workflows API"
}

resource "aws_lambda_function" "authorizer" {
  function_name = "labcas-${var.maturity}-workflows-authorizer"
  runtime       = "python3.13"
  handler       = "authorizer.lambda_handler"
  layers = [aws_lambda_layer_version.layer.arn]

  filename         = data.archive_file.lambda_authorizer_zip.output_path
  source_code_hash = data.archive_file.lambda_authorizer_zip.output_base64sha256

  role   = var.lambda_role_arn
  timeout = 30
  memory_size = 512

  environment {
    variables = {
      STAGE = var.stage
    }
  }
}
