locals {
  shared_env = {
    STAGE                = var.stage
    S3_BUCKET_STAGING    = var.s3_bucket_staging
    MWAA_ENV_NAME        = var.mwaa_env_name
    REGION               = var.aws_region
    JWT_SECRET_KEY_ARN   = var.jwt_secret_arn
  }

  layers_watched_dir = "${path.module}/src/layer"

  layer_files = fileset(local.layers_watched_dir, "**")

  layer_files_hash = sha256(join("", [
    for f in local.layer_files :
    filesha256("${local.layers_watched_dir}/${f}")
  ]))

}

resource "null_resource" "prepare_layer" {
  triggers = {
    files_hash = local.layer_files_hash
    build_layer_exists = fileexists("${path.module}/build/layer") ? "yes" : "no"
  }
  provisioner "local-exec" {
    command = "rm -fr ${path.module}/build/layer/python && mkdir -p ${path.module}/build/layer/ && cp -r  ${path.module}/src/layer ${path.module}/build/layer/python && pip install -r ${path.module}/build/layer/python/requirements.txt -t ${path.module}/build/layer/python"
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
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = local.shared_env
  vpc_subnet_ids = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids
}

module "listruns_lambda" {
  source      = "../lambda_function"
  api_function_name = "listruns"
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = local.shared_env
  vpc_subnet_ids = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids

}

module "listworkflows_lambda" {
  source      = "../lambda_function"
  api_function_name = "listworkflows"
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = local.shared_env
  vpc_subnet_ids = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids

}


module "createrun_lambda" {
  source      = "../lambda_function"
  api_function_name = "createrun"
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = local.shared_env
  vpc_subnet_ids = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids

}

module "updateoutput_lambda" {
  source      = "../lambda_function"
  api_function_name = "updateoutput"
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = local.shared_env
  vpc_subnet_ids = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids

}

module "describeworkflow_lambda" {
  source      = "../lambda_function"
  api_function_name = "describeworkflow"
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = local.shared_env
  vpc_subnet_ids = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids

}

module "browseoutputs_lambda" {
  source      = "../lambda_function"
  api_function_name = "browseoutputs"
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = local.shared_env
  vpc_subnet_ids = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids

}

module "notimplemented_lambda" {
  source      = "../lambda_function"
  api_function_name = "notimplemented"
  maturity    = var.maturity
  layers      = [aws_lambda_layer_version.layer.arn]
  lambda_role_arn = var.lambda_role_arn
  environment_variables = local.shared_env
  vpc_subnet_ids = var.vpc_subnet_ids
  vpc_security_group_ids = var.vpc_security_group_ids

}


