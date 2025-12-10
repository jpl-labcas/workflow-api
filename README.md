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

### Layer

A layer is a lambda component containing re-usable functions. We use it for the code helping to connect to the restful API.

Package it as follows:


    cd ./aws/layers/labcas-mwaa-restful-api-connection
    zip -r labcas-mwaa-restful-api-connection.zip *

Upload the zip file as a layer in the AWS console.


### Lambda functions





## Generate doc manually


     pip install -e '.[dev]'
     cd docs
     cp openapi.yml _build/html/_static
     make html

Test the web site created:

    cd _build/html
    python -m http.server 8000

Use your browser to go to `http://localhost:8000` and check the documentation.







