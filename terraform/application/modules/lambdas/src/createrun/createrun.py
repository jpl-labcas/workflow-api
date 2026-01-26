import os
import json
import yaml
import logging
import boto3
import requests
from datetime import datetime

from session_info import get_session_info

OUTPUT_BUCKET = "edrn-labcas-workflow-outputs"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

aws_session_token = os.environ.get('AWS_SESSION_TOKEN')


def load_config():
    logger.debug("Load API config")
    ssm_client = boto3.client('ssm')
    # Retrieve /labcas/workflow/api/config from Parameter Store using extension cache
    parameter_name = "/labcas/workflow/api/config"
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    logger.debug("launch query to get config fro parameter store")
    config = response['Parameter']['Value']
    return yaml.safe_load(config)


def trigger_dag(region, env_name, dag_name, dag_params):
    """
    Triggers a DAG in a specified MWAA environment using the Airflow REST API.

    Args:
    region (str): AWS region where the MWAA environment is hosted.
    env_name (str): Name of the MWAA environment.
    dag_name (str): Name of the DAG to trigger.
    """

    logger.info(f"Attempting to trigger DAG {dag_name} in environment {env_name} at region {region}")

    # Retrieve the web server hostname and session cookie for authentication
    try:
        web_server_host_name, session_cookie = get_session_info(region, env_name)
        if not session_cookie:
            logging.error("Authentication failed, no session cookie retrieved.")
            return
    except Exception as e:
        logging.error(f"Error retrieving session info: {str(e)}")
        return

    # Prepare headers and payload for the request
    cookies = {"session": session_cookie}
    json_body = {"conf": dag_params}

    # Construct the URL for triggering the DAG
    url = f"https://{web_server_host_name}/api/v1/dags/{dag_name}/dagRuns"

    # Send the POST request to trigger the DAG
    try:
        response = requests.post(url, cookies=cookies, json=json_body)
        # Check the response status code to determine if the DAG was triggered successfully
        if response.status_code == 200:
            logging.info("DAG triggered successfully.")
            return response.json()
        else:
            logging.error(f"Failed to trigger DAG: HTTP {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Request to trigger DAG failed: {str(e)}")


def lambda_handler(event, context):
    mwaa_env_name = 'edrn-dev-airflow'
    region = "us-west-2"
    try:
        logger.debug(event)

        stage_variables = event.get('stageVariables', {})
        allow_origin_value = stage_variables.get('allowOrigin', "")
        logger.info("Allowed Origin is %s", allow_origin_value)

        # get username from authorizer context
        requestContext = event.get('requestContext', {})
        logger.debug(requestContext)
        authorizer = requestContext.get('authorizer', {})
        logger.debug(authorizer)
        username = authorizer.get('username', {})

        dag_name = event.get("pathParameters", {}).get("id")

        # body is a string initially
        body = json.loads(event['body'])

        config = load_config()
        collection_id = body["in_data_selection"]
        if collection_id not in config["collections"]:
            logger.debug(config)
            return {
                "statusCode": 400,
                "body": f"collection {collection_id} is unknown"
            }

        # Make input parameters for the workflow
        # keep all parameters for traceability
        dag_params = body
        input_collection = config["collections"][collection_id]

        # add internal location of the input data-selection
        dag_params["in_bucket"] = input_collection["bucket"]
        dag_params["in_prefix"] = input_collection["prefix"]

        # Add output location params which are notdecided by the user.
        dag_params["out_bucket"] = OUTPUT_BUCKET
        # we avoid special character to make the string URL friendly, for later access
        datetime_now = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        dag_params["out_prefix"] = f"{username}/{datetime_now}"
        # Add the username for traceability
        dag_params["username"] = username

        # Trigger the DAG with the provided arguments
        response = trigger_dag(region, mwaa_env_name, dag_name, dag_params)

        return {
            "statusCode": 201,
            "body": json.dumps({
                "run_id": response['dag_run_id'],
                "state": response['state']
            }),
            "headers": {
                "Access-Control-Allow-Origin": allow_origin_value,
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            }
        }

    except (json.JSONDecodeError, TypeError):
        return {
            "statusCode": 400,
            "body": "Invalid JSON format in the request body",
            "headers": {
                "Access-Control-Allow-Origin": allow_origin_value,
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            }
        }