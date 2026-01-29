Installation
=============================

This section describes how to install the LabCas Workflow API on AWS.

LabCas Workflows is meant to be installed on an Amazon Web Service account.

Prerequisites
~~~~~~~~~~~~~~~~

What you need to install LabCas Workflows is:

* System administrator support to comply with the security constraints defined by your organization.
* An AWS account with a VPC and private subnets
* a running (MWAA)[https://jpl-labcas.github.io/workflows/install.html#workflow-engine-setup] (Managed Workflows for Apache Airflow) environment with a t least one DAG deployed. Some input data for this DAG should be in a S3 bucket (see next item).
* an S3 bucket where the collection data files are stored
* an S3 bucket where the output data files are staged.
* an S3 bucket to store the terraform state files.
* a security group allowing the lambda functions to access MWAA and S3 services (outbound access to all traffic is usually allowed by default).

Some knowledge of the AWS console and AWS CLI is helpful.



Architecture Overview
~~~~~~~~~~~~~~~~~~~~~~
The LabCas workflow API is a sub-component of the `LabCas Workflows documentation <https://jpl-labcas.github.io/workflows/>`_ system, which relies on several AWS services to function properly.

See the architecture diagram in the `LabCas Workflows documentation <https://jpl-labcas.github.io/workflows/install.html#architecture-overview>`_ for more details on the high level architecture.

The API component is responsible for handling RESTFul API requests, managing workflow definitions, and orchestrating workflow executions. It interacts with other components such as the workflow engine (e.g., Apache Airflow) and storage services (e.g., S3 buckets) by providing logical access (workflows, datasets) to the users according to their authorizations and without exposing the actual infrastructure (workflow engine, computing resources, storage).

The API is deployed as an AWS/API Gateway. Each API endpoint correspond to specific functions implemented with AWS/Lambda functions that process the requests and interact with other AWS services as needed.


.. mermaid::

   graph TD
     subgraph LabCas API
       F[AWS API Gateway]
       J[Authorizer Lambda]
       K[Implementation Lambda Functions]
       F --> J
       F --> K
     end
     subgraph LabCas Workflows
       G[Workflow_Engine_Airflow]
       H[(DAG_S3_bucket)]
       I[(Staging_S3_bucket)]
       K --> G
       K --> I
       G --> H
       G --> I
     end

Doing the Installation
~~~~~~~~~~~~~~~~~~~~~~~

Create the implementation lambda functions
-------------------------------------------

Parameters
^^^^^^^^^^^

Create a parameter in the Parameter Store of the AWS System Manager, with reference name ``/labcas/workflow/api/config``:

The YAML content is as follows (update the values as needed)::

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


Secrets
^^^^^^^^

To decode the JWT token used to authenticate the requests as key is needed. Request it from your LabCas Core administrator and store it in the AWS secret manager as a plaintext secret with name ``jwtSecret``.
Keep the ARN of the secret for the next steps.

lambda role
^^^^^^^^^^^

Create an IAM role for the lambda functions with the following policies:

- AWSLambdaBasicExecutionRole
- AWSLambdaVPCAccessExecutionRole
- And a specific policy to access:
  - MWAA: Full Read, Limited Write
  - S3 Limited to the staging bucket and archive bucket: List, Read, Write
  - Systems Manager Limited on dedicated config parameter: Read
  - Secrets Manager Limited on dedicated JWT secret: Read

The custom policy should look like the following (update the ARNs as needed)::


  {
    "Statement": [
        {
            "Action": [
                "airflow:ListEnvironments",
                "airflow:GetEnvironment",
                "airflow:ListTagsForResource",
                "airflow:CreateCliToken"
            ],
            "Effect": "Allow",
            "Resource": "{MWAA environment ARN}"
        },
        {
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Effect": "Allow",
            "Resource": "{JWT secret ARN}"
        },
        {
            "Action": [
                "airflow:InvokeRestApi",
                "airflow:CreateWebLoginToken"
            ],
            "Effect": "Allow",
            "Resource": "{ARN of the MWAA execution role}/User"
        },
        {
            "Action": [
                "ssm:GetParameters",
                "ssm:GetParameter"
            ],
            "Effect": "Allow",
            "Resource": [
                "{ARN for the parameter store parameter /labcas/workflow/api/config}"
            ]
        },
        {
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "s3:PutObject"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:s3:::{Staging output bucket name}/*",
                "arn:aws:s3:::{Staging output bucket name}"
            ]
        },
        {
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:lambda:{your AWS region}:{your account number}:function:labcas*"
        }
    ],
    "Version": "2012-10-17"
  }



Layer
^^^^^^^^^^^

Layer deployment is part of the terraform deployment of the lambda functions, so the following sub-section is optional.

Manual layer deployment
```````````````````````

A layer is a lambda component containing re-usable functions. We use it for the code helping to connect to the restful API.

Package it as follows::

    cd ./terraform/applications/modules/lambdas/
    rm -fr build
    pip install -r requirements.txt -t src/layer/python
    cd src/layer/python
    zip -r labcas-mwaa-restful-api-connection.zip *

Upload the zip file as a layer in the AWS console.

Lambda functions
^^^^^^^^^^^^^^^^^

Terraform is used to deploy the lambda functions.

Create your deployment environment directory::

    mkdir terraform/environments/your_tenant_your_venue_dev

Create a terraform state configuration file ``terraform/environments/your_tenant_your_venue_dev/terraform.tfvars`` with content similar to::

    # Terraform backend configuration for remote state
    bucket = "<an S3 bucket for your terraform state>"
    key    = "labcas.tfstate"
    aws_region = "<your AWS regision, e.g. us-west-1>"

Create a variables file for your deployment configuration in a local file ``terraform/environments/your_tenant_your_venue_dev/variables.tfvars`` with content similar to::

    maturity={Maturity level of the deployment (poc: aws console exploration, iac: terraform deployment, ops: full automation with CICD or SA documented procedures)}
    stage={name of a API deployment, stage in AWS API gateway, e.g. dev}
    lambda_role_arn={lambda AM role defined above}
    aws_region={your AWS region, e.g. us-west-1}
    aws_profile={your AWS CLI profile to use}
    jwt_secret_arn={the ARN for JWT key that you stored in AWS Secret Manager, as describe above}
    s3_bucket_staging={the S3 bucket where the workflow output data is staged}
    mwaa_env_name={the MWAA environment name where the workflows are deployed}
    stage={the name of your API deployment}
    vpc_subnet_ids = ["subnet-private-example1","subnet-private-example2, , see preriquisites above"]
    vpc_security_group_ids = ["sg-example1, see preriquisites above"]



Maturity aims at avoid naming conflict between different maturity of deployment in the same AWS account.
The AWS resources created with the terraform script provided contains the chosen maturity value (poc, iac, ops).
Any of these values can be used in a dev venue, only the ops or iac can be used in production venues. The openapi.yml file provided in the docs refers to the maturity value "iac".

Deploy the lambda functions with terraform::

    cd terraform/application/modules/lambdas
    terraform init -backend-config=../../../environments/your_tenant_your_venue_dev/terraform.tfvars
    terraform validate
    terraform plan -var-file=../../../environments/your_tenant_your_venue_dev/variables.tfvars
    terraform apply -var-file=../../../environments/your_tenant_your_venue_dev/variables.tfvars

To undeploy, as needed::

    terraform destroy -var-file=../../../environments/your_tenant_your_venue_dev/variables.tfvars


Create the API Gateway
-----------------------

Deploy the API Gateway
^^^^^^^^^^^^^^^^^^^^^^^

Use the AWS console to create a new API gateway (REST API).

Import the file `./docs/openapi.yml` to create the API structure.

This will connect the API endpoints to the lambda functions created above.


Test the API
^^^^^^^^^^^^^

A demo UI is provided to demonstrate the API features.

Follow instructions in the (workflow-api-client-demo repository)[https://github.com/jpl-labcas/workflow-api-client-demo]












