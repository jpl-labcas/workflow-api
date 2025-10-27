# Science Workflow Execution API

A RESTFul API for managing LabCas workflows.

This comes in 2 implementations:
 - A Flask-based REST API service
 - An AWS API gateway + lambda 

# API gateway + lambda

## Lambda deployment:

### Layer

A layer is a lambda component containing re-usable functions. We use it for the code helping to connect to the restful API.

Package it as follows:


    cd ./aws/layers/labcas-mwaa-restful-api-connection
    zip -r labcas-mwaa-restful-api-connection.zip *

Upload the zip file as a layer in the AWS console.










