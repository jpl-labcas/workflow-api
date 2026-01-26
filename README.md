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

See doc in gh-pages, install page.


## Generate doc manually


     pip install -e '.[dev]'
     cd docs
     make html

Test the web site created:

    cd _build/html
    python -m http.server 8000

Use your browser to go to `http://localhost:8000` and check the documentation.







