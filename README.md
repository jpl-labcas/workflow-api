# Science Workflow Execution API

A RESTFul API for managing LabCas workflows.

This comes in 2 implementations:
 - A Flask-based REST API service (obsolete)
 - An AWS API gateway + lambda 

# Reference specification

The reference OpenAPI specification is in the file `./docs/openapi.yml`.

# API gateway + lambda

## Create the API gateway

Use the AWS console to create a new API gateway (REST API).

Import the file `./docs/openapi.yml` to create the API structure.


## Lambda deployment:

### Parameters

Create a parameter in the Parameter Store of the AWS System Manager, with reference name `/labcas/workflow/api/config`:

The YAML content is as follows (update the values as needed):

`
collections:
    {archive dataset name 1}:
        bucket: {s3 bucket where the  data is stored}
        prefix: {s3 prefix where the data is stored in the above bucket}/
        workflows:
            {id of a deployed airflow workflow (aka DAG)}:
               authorized_users:
                  - {authorized user 1, using labcas authentication}
                  - {authorized user 2, using labcas authentication}
                  - ...
    {archive dataset name 1}:
        ...
`


### lambda role

Create an IAM role for the lambda functions with the following policies:

- AWSLambdaBasicExecutionRole
- AWSLambdaVPCAccessExecutionRole
- And a specific policy to access:
  - MWAA Full: Read Limited: Write
  - S3 Limited to the staging bucket and archive bucket: List, Read, Write
  - Systems Manager Limited on dedicated config parameter: Read
 
### Layer

Layer deployment is part of the terraform deployment of the lambda functions.

#### Manual layer deployment
A layer is a lambda component containing re-usable functions. We use it for the code helping to connect to the restful API.

Package it as follows:


    cd ./terraform/applications/modules/lambdas/
    rm -fr build
    pip install -r requirements.txt -t src/layer/python
    cd src/layer/python
    zip -r labcas-mwaa-restful-api-connection.zip *

Upload the zip file as a layer in the AWS console.


### Lambda functions

Terraform is used to deploy the lambda functions.

Create your deployment environment directory:

    mkdir terraform/environments/your_tenant_your_venue_dev

Create a terraform state configuration file `terraform/environments/your_tenant_your_venue_dev/terraform.tfvars` with content similar to:

    # Terraform backend configuration for remote state
    bucket = "<an S3 bucket for your terraform state>"
    key    = "labcas.tfstate"
    region = "<your AWS regision, e.g. us-west-1>"   

Create a variables file for your deployment configuration in a local file `terraform/environments/your_tenant_your_venue_dev/variables.tfvars` with content similar to:

    maturity={Maturity level of the deployment (poc: aws console exploration, iac: terraform deployment, ops: full automation with CICD or SA documented procedures)}
    stage={name of a API deployment, stage in AWS API gateway, e.g. dev}
    lambda_role_arn={lambda AM role defined above}
    aws_region={your AWS regision, e.g. us-west-1}
    aws_profile={you AWS CLI profile to use}

Maturity aims at avoid naming conflict between different maturity of deployment in the same AWS account.
The AWS resources created with the terraform script provided contains the chosen maturity value (poc, iac, ops).
All those value can be used in a dev venue, only the ops or iac can be used in production venues.


Deploy the lambda functions with terraform:

    

    cd terraform/application/modules/lambdas
    terraform init -backend-config=../../../environments/your_tenant_your_venue_dev/terraform.tfvars
    terraform validate
    terraform plan -var-file=../../../environments/your_tenant_your_venue_dev/variables.tfvars
    terraform apply -var-file=../../../environments/your_tenant_your_venue_dev/variables.tfvars



## Test the API

A demo UI is provided to demonstrate the API features.

Follow instructions in the (workflow-api-client-demo repository)[https://github.com/jpl-labcas/workflow-api-client-demo]


## Generate doc manually


     pip install -e '.[dev]'
     cd docs
     make html

Test the web site created:

    cd _build/html
    python -m http.server 8000

Use your browser to go to `http://localhost:8000` and check the documentation.







