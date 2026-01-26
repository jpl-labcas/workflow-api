import json
import logging
import boto3
import json
import requests

from session_info import get_session_info

logging.basicConfig(level=logging.INFO)


def info_dag(region, env_name, dag_name):
    """
    Triggers a DAG in a specified MWAA environment using the Airflow REST API.

    Args:
    region (str): AWS region where the MWAA environment is hosted.
    env_name (str): Name of the MWAA environment.
    dag_name (str): Name of the DAG to trigger.
    """

    logging.info(f"Attempting to get DAG {dag_name} information in environment {env_name} at region {region}")

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
    url = f"https://{web_server_host_name}/api/v1/dags/{dag_name}"

    # Send the GET request to get DAG's information
    try:
        response = requests.get(url, cookies=cookies)
        # Check the response status code to determine if the DAG was triggered successfully
        if response.status_code == 200:
            logging.info("DAG info requested successfully.")
            return response.json()
        else:
            logging.error(f"Failed to get DAG's information: HTTP {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Request to get DAG's information failed: {str(e)}")

def lambda_handler(event, context):
    ## TODO complete implementation
    mwaa_env_name = 'edrn-dev-airflow'  # <-- Change this
    region = "us-west-2"
    # hardcoded for tests, parameter should come from the path
    dag_name = "nebraska"

    # list the DAGs with the provided arguments
    info_dag = info_dag(region, mwaa_env_name, dag_name)

    return {
        "statusCode": 501,
        "body": "This endpoint is not implemented yet."
    }