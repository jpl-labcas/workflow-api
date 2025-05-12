import json

import boto3
import json
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import get_session

def lambda_handler(event, context):
    mwaa_env_name = 'edrn-dev-airflow'  # <-- Change this

    mwaa_client = boto3.client('mwaa')
    region = boto3.session.Session().region_name

    # Step 1: Get environment info
    env = mwaa_client.get_environment(Name=mwaa_env_name)
    hostname = env['Environment']['AirflowWebServerHostname']

    # Step 2: Prepare API call
    endpoint = f"https://{hostname}/aws_mwaa/cli"
    command = "dags list"
    payload = json.dumps({"cli": command})

    # Step 3: Sign the request
    session = get_session()
    creds = session.get_credentials()
    req = AWSRequest(method="POST", url=endpoint, data=payload, headers={"Content-Type": "application/json"})
    SigV4Auth(creds, "airflow", region).add_auth(req)
    signed_headers = dict(req.headers.items())

    # Step 4: Make the request
    response = requests.post(endpoint, headers=signed_headers, data=payload)

    # Return the CLI output (it's in the `stdout` field)
    try:
        result = response.json()
        return {
            'statusCode': 200,
            'dags': result.get('stdout', 'No output')
        }
    except Exception as e:
        return {
            'statusCode': response.status_code,
            'error': str(e),
            'raw': response.text
        }



