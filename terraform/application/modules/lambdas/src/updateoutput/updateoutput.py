import os
import io
import json
import boto3
import botocore
import logging
import configparser

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get("S3_BUCKET_STAGING")
ROOT_PREFIX = ""

def lambda_handler(event, context):

    logger.debug(event)

    stage_variables = event.get('stageVariables', {})
    allow_origin_value = stage_variables.get('allowOrigin')
    logger.info("Allowed Origin is %s", allow_origin_value)

    # get username from authorizer context
    requestContext = event.get('requestContext', {})
    logger.debug(requestContext)
    authorizer = requestContext.get('authorizer', {})
    logger.debug(authorizer)
    username = authorizer.get('username', {})

    base_prefix =  os.path.join(ROOT_PREFIX, username)

    # body is a string initially
    body = json.loads(event['body'])

    prefix = body.get("prefix", "")
    full_prefix = os.path.join(base_prefix, prefix)

    # save metadata in .cfg files
    saved_metadata = []
    for file_name, file_obj in body.get("files", {}).items():
        if "properties" in file_obj:
            try:
                # we don't use the data file but we want to make sure it exists
                data_file_key = os.path.join(full_prefix, file_name)
                logger.debug("Test if data object %s exists", data_file_key)
                s3.head_object(Bucket=BUCKET_NAME, Key=data_file_key)

                config = configparser.ConfigParser()
                # keep the field names with the original case
                config.optionxform=str

                # update the properties in the config-like content
                config.add_section(file_name)
                properties = file_obj["properties"]
                for k, v in properties.items():
                    config.set(file_name, k, v)

                # Write the updated config to a string
                config_buffer = io.StringIO()
                config.write(config_buffer)
                updated_config_content = config_buffer.getvalue()

                # Upload the updated config to S3
                cfg_file_key = data_file_key + ".cfg"
                logger.info("Saving metadata in object %s", cfg_file_key)
                s3.put_object(Bucket=BUCKET_NAME, Key=cfg_file_key, Body=updated_config_content)
                saved_metadata.append(file_name)

            except botocore.exceptions.ClientError as e:
                msg = f"Try to load metadata a file which does not exists {os.path.join(prefix, file_name)}"
                logger.error(msg)
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": allow_origin_value,
                        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization"
                    },
                    "body": msg
                }


    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": allow_origin_value,
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        },
        "body": f"metadata saved for files: {", ".join(saved_metadata)}"
    }
