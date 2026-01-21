import os
import json
import yaml
import logging
import boto3
import requests

from session_info import get_session_info

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


def list_dags(region, env_name):
    """
    Triggers a DAG in a specified MWAA environment using the Airflow REST API.

    Args:
    region (str): AWS region where the MWAA environment is hosted.
    env_name (str): Name of the MWAA environment.
    dag_name (str): Name of the DAG to trigger.
    """

    logging.info(f"Attempting to list DAGs in environment {env_name} at region {region}")

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
    json_body = {"conf": {}}

    # Construct the URL for triggering the DAG
    url = f"https://{web_server_host_name}/api/v1/dags"

    # Send the POST request to trigger the DAG
    try:
        response = requests.get(url, cookies=cookies)
        # Check the response status code to determine if the DAG was triggered successfully
        if response.status_code == 200:
            logging.info("DAGs listed successfully.")
            return response.json()
        else:
            logging.error(f"Failed to list DAGs: HTTP {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Request to list DAGs failed: {str(e)}")


def lambda_handler(event, context):
    logger.debug(event)

    mwaa_env_name = 'edrn-dev-airflow'  # <-- Change this
    region = "us-west-2"

    # list the DAGs with the provided arguments
    dag_list = list_dags(region, mwaa_env_name)["dags"]

    # format response
    workflows = [dict(id=dag["dag_id"], description=dag["description"]) for dag in dag_list]

    # get username from authorizer context
    requestContext = event.get('requestContext', {})
    logger.debug(requestContext)
    authorizer = requestContext.get('authorizer', {})
    logger.debug(authorizer)
    username = authorizer.get('username', {})

    # collection id is in the path only for end-point /collections/{collection_id}/workflows , we support also /workflows (without collection id)
    query_parameters = event.get('queryStringParameters', {})
    data_id = query_parameters.get('data_id', "")
    config = load_config()
    if data_id:
        logger.info("searching for workflows application for data-selection %s", data_id)
        collection = config["collections"].get(data_id, {})

        if collection == {}:
            logger.debug(config)
            return {
                "statusCode": 404,
                "body": f"collection {data_id} is unknown"
            }
        logger.debug("collection object found in config %s", collection)
        collection_workflows = collection.get("workflows", {})
        logger.debug("collection %s enables following workflow %s", data_id, collection_workflows)
        authorized_workflows = [k for k, w in collection_workflows.items() if username in w.get("authorized_users", [])]
        logger.debug("authorized worflows are %s", authorized_workflows)
        filtered_workflows = []
        for w in workflows:
            logger.debug("filterning %s", w['id'])
            if w['id'] in authorized_workflows:
                logger.debug("keepning it")
                filtered_workflows.append(w)
            else:
                logger.debug("rejecting it")
        workflows = filtered_workflows

    stage_variables = event.get('stageVariables', {})
    allow_origin_value = stage_variables.get('allowOrigin', '')
    logger.info("Allowed Origin is %s", allow_origin_value)

    return {
        "statusCode": 200,
        "body": json.dumps(dict(workflows=workflows)),
        "headers": {
            "Access-Control-Allow-Origin": allow_origin_value,
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        }
    }
