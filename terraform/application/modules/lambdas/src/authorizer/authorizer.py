import json
import logging
import yaml
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

JWT_ALGORITHM = 'HS256'
REGION_NAME = 'us-west-2'


class KeyNotFoundException(Exception):
    pass


class TokenNotFoundException(Exception):
    pass


# TODO extract users from config to avoid duplication of configuration
def load_config():
    logger.debug("Load API config")
    ssm_client = boto3.client('ssm')
    # Retrieve /labcas/workflow/api/config from Parameter Store using extension cache
    parameter_name = "/labcas/workflow/api/config"
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    logger.debug("launch query to get config fro parameter store")
    config = response['Parameter']['Value']
    return yaml.safe_load(config)


def get_authorized_users():
    # config as the shape
    # collections:
    # nebraska_images:
    #     bucket: edrn-bucket
    #     prefix: nebraska_images/
    #     workflows:
    #         nebraska:
    #            authorized_users:
    #               - thomas
    #               - dliu
    config = load_config()
    authorized_users = set()
    collections = config.get("collections", {})
    logger.debug("the collections: %s", collections)
    for c in collections.values():
        logger.debug(c)
        workflows = c.get("workflows", {})
        for w in workflows.values():
            users = w.get("authorized_users", {})
            logger.debug("found authorized users %s", users)
            for u in users:
                authorized_users.add(u)
    return authorized_users


def get_jwt_secret():
    client = boto3.client('secretsmanager', region_name=REGION_NAME)
    response = client.get_secret_value(SecretId="arn:aws:secretsmanager:us-west-2:300153749881:secret:jwtSecret-CqRUNy")
    if 'SecretString' in response:
        return response['SecretString']
    else:
        logger.error("Key not found. Response from boto3/secretsmanager/get_secret_value is %s", response)
        raise KeyNotFoundException("JWT Token decoding key not found in Secret Manager")


def lambda_handler(event, context):
    try:

        token = get_token_from_event(event)

        jwt_secret = get_jwt_secret()
        decoded = jwt.decode(token, key=jwt_secret, algorithms=[JWT_ALGORITHM], issuer="LabCAS", audience="LabCAS")

        logger.debug(decoded)
        user_string = decoded.get('username') or decoded.get('sub') or 'unknown'
        claims = None  # TODO to be completed

        # Log or use these as needed
        logger.info(f"Authenticated user: {user_string}")
        logger.info(f"Claims: {json.dumps(claims)}")

        # patter for a username string  "uid=thomas,dc=edrn,dc=jpl,dc=nasa,dc=gov"
        user_string_split = [tuple(key_value.split("=")) for key_value in user_string.split(",")]
        username = user_string_split[0][1]
        context = {"username": username, "role": claims}
        if username in get_authorized_users():
            return generate_policy(user_string, 'Allow', event['methodArn'], context=context)
        else:
            return generate_policy('anonymous', 'Deny', event['methodArn'])

    except TokenNotFoundException as e:
        logger.error("Token not found in query.")
        return generate_policy('anonymous', 'Deny', event['methodArn'])
    except ExpiredSignatureError:
        logger.error("Token has expired")
        return generate_policy('anonymous', 'Deny', event['methodArn'])
    except InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        return generate_policy('anonymous', 'Deny', event['methodArn'])
    except  KeyNotFoundException as e:
        logger.error(f"Token decoding key not found: {str(e)}")
        return generate_policy('anonymous', 'Deny', event['methodArn'])


def get_token_from_event(event):
    logger.debug(event)
    auth_header = event.get('headers', {}).get('authorization')
    if auth_header.startswith('Bearer '):
        return auth_header[len('Bearer '):]
    raise TokenNotFoundException("Token not found in query.")


def generate_policy(principal_id, effect, resource, context=None):
    auth_response = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        }
    }

    if context:
        # Optional: send context back to your API
        auth_response['context'] = {
            k: str(v) for k, v in context.items() if isinstance(v, (str, int, float, bool))
        }
    logger.info(auth_response)
    return auth_response
