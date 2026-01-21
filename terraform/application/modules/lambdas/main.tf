resource "null_resource" "prepare_layer" {
  triggers = {
    requirements_hash = filesha256("${path.module}/requirements.txt")
  }
  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/build/layer/python && pip install -r requirements.txt -t ${path.module}/build/layer/python"
  }
}

data "archive_file" "lambda_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build/layer"
  output_path = "${path.module}/build/layer.zip"
  depends_on  = [null_resource.prepare_layer]
}



resource "aws_lambda_layer_version" "layer" {
  layer_name          = "labcas-${var.maturity}-workflows-layer"
  filename            = data.archive_file.lambda_layer_zip.output_path
  compatible_runtimes = ["python3.13"]
  description         = "Common dependencies for LabCAS workflows API"
  depends_on = [data.archive_file.lambda_layer_zip]
}

module "authorizer_lambda" {
  source      = "../lambda_function"
  api_function_name = "authorizer"
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = {
    STAGE = var.stage
  }
}

module "listruns_lambda" {
  source      = "../lambda_function"
  api_function_name = "listruns"
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = {
    STAGE = var.stage
  }
}

module "listworkflows_lambda" {
  source      = "../lambda_function"
  api_function_name = "listworkflows"
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = {
    STAGE = var.stage
  }
}


module "createrun_lambda" {
  source      = "../lambda_function"
  api_function_name = "createrun"
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = {
    STAGE = var.stage
  }
}

module "updateoutput_lambda" {
  source      = "../lambda_function"
  api_function_name = "updateoutput"
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = {
    STAGE = var.stage
  }
}

module "describeworkflow_lambda" {
  source      = "../lambda_function"
  api_function_name = "describeworkflow"
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = {
    STAGE = var.stage
  }
}


