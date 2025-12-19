import json
import logging
import boto3
import json
import requests

from session_info import get_session_info

logging.basicConfig(level=logging.INFO)

def trigger_dag(region, env_name, dag_name):
    """
    Triggers a DAG in a specified MWAA environment using the Airflow REST API.

    Args:
    region (str): AWS region where the MWAA environment is hosted.
    env_name (str): Name of the MWAA environment.
    dag_name (str): Name of the DAG to trigger.
    """

    logging.info(f"Attempting to trigger DAG {dag_name} in environment {env_name} at region {region}")

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
    mwaa_env_name = 'edrn-dev-airflow'  # <-- Change this
    region = "us-west-2"
    dag_name = event.get("body", {}).get("workflow_id")
    dag_params = event.get("body", {}).get("params")

    # Trigger the DAG with the provided arguments
    response = trigger_dag(region, mwaa_env_name, dag_name)

    return {
        "statusCode": 201,
        "body": {
            "run_id": response['dag_run_id'],
            "state": response['state']
        }
    }