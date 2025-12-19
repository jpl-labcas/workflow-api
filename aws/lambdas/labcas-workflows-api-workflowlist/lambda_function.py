import json
import logging
import boto3
import json
import requests

from session_info import get_session_info

logging.basicConfig(level=logging.INFO)


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
    mwaa_env_name = 'edrn-dev-airflow'  # <-- Change this
    region = "us-west-2"

    # list the DAGs with the provided arguments
    dag_list = list_dags(region, mwaa_env_name)["dags"]

    # format response
    workflows = [dict(id=dag["dag_id"], description=dag["description"]) for dag in dag_list]
    return dict(workflows=workflows)