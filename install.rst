Installation
=============================

This section describes how to install the LabCas Workflow API on AWS.

LabCas Workflows is meant to be installed on an Amazon Web Service account.

Prerequisites
~~~~~~~~~~~~~~~~

What you need to install LabCas Workflows is:

* System administrator support to comply with the security constraints defined by your organization.
* An AWS account with a VPC and private subnets

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




Create the API Gateway
-----------------------

The API gateway is


Create the authorizer Lambda function










