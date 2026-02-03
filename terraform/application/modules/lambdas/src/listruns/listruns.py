import os
import json
import logging
import boto3
import requests
import posixpath

from session_info import get_session_info

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

AWS_REGION = os.environ['REGION']
MWAA_ENV_NAME = os.environ['MWAA_ENV_NAME']
OUTPUT_RESULT_API_PATH = 'output-data'


# TODO update when we have a DNS for it
def get_output_base_url(event):
    headers = event.get("headers", {})
    http_schema = headers.get("X-Forwarded-Proto", "")
    api_base_url = headers.get("Host", "")
    api_base_url = f"{http_schema}://{api_base_url}"

    requestContext = event.get("requestContext", {})
    stage = requestContext.get("stage", "")

    stage_base_url = posixpath.join(api_base_url, stage)
    return posixpath.join(stage_base_url, OUTPUT_RESULT_API_PATH)


def list_runs(region, env_name, dag_name):
    """
    Triggers a DAG in a specified MWAA environment using the Airflow REST API.

    Args:
    region (str): AWS region where the MWAA environment is hosted.
    env_name (str): Name of the MWAA environment.
    dag_name (str): Name of the DAG to trigger.
    """

    logging.info(f"Attempting to list DAG's runs in environment {env_name} at region {region}")

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
    url = f"https://{web_server_host_name}/api/v1/dags/{dag_name}/dagRuns"

    # Send the POST request to trigger the DAG
    try:
        response = requests.get(url, cookies=cookies)
        # Check the response status code to determine if the DAG was triggered successfully
        if response.status_code == 200:
            logging.info("DAGs listed successfully.")
            return response.json()
        else:
            logging.error(f"Failed to list runs: HTTP {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Request to list runs failed: {str(e)}")


def short_run(run, api_output_base_url: str):
    logger.debug(run)

    # get the relative HTTP URL to the data
    conf = run.get('conf', {})
    s3_out_prefix = conf.pop('out_prefix', "")
    out_path = s3_out_prefix.split("/")[-1]
    logger.debug("output path %s", out_path)
    out_url = posixpath.join(api_output_base_url, out_path)
    logger.debug("output url %s", out_url)

    # remove internal workflow parameters that we don't want to share
    _ = conf.pop("out_bucket", "")
    _ = conf.pop("in_bucket", "")
    _ = conf.pop("in_prefix", "")
    _ = conf.pop("username", "")

    return {
        'run_id': run['dag_run_id'],
        'workflow_id': run['dag_id'],
        'status': run['state'],
        'start_time': run['start_date'],
        'output_url': out_url,
        'conf': conf
    }


def lambda_handler(event, context):

    logger.debug("event %s", event)
    logger.debug("contet %s", context)

    # context['requestContext']['domainName'] and the API stage in context['requestContext']['stage']

    dag_name = event.get("pathParameters", {}).get("id")

    # list the DAGs with the provided arguments
    run_list = list_runs(AWS_REGION, MWAA_ENV_NAME, dag_name)["dag_runs"]

    # get username from authorizer context
    requestContext = event.get('requestContext', {})
    logger.debug(requestContext)
    authorizer = requestContext.get('authorizer', {})
    logger.debug(authorizer)
    username = authorizer.get('username', {})

    # format response, filter out runs of other users
    api_output_base_url = get_output_base_url(event)
    runs = [short_run(run, api_output_base_url) for run in run_list if
            username == run.get('conf', {}).get("username", "")]

    logger.info("run list is ready")

    stage_variables = event.get('stageVariables', {})
    allow_origin_value = stage_variables.get('allowOrigin')
    logger.info("Allowed Origin is %s", allow_origin_value)

    return {
        "statusCode": 200,
        "body": json.dumps(dict(runs=runs)),
        "headers": {
            "Access-Control-Allow-Origin": allow_origin_value,
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        }
    }
