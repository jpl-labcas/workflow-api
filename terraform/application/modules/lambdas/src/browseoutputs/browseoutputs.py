import boto3
import os
import logging
import json
import configparser

config = configparser.ConfigParser()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

s3 = boto3.client('s3')
BUCKET_NAME = os.environ["S3_BUCKET_STAGING"] # Set in Lambda env vars
ROOT_PREFIX = ""


def cfg_to_json(cfg: str):
    """cfg is the content of a cfg file """
   # Parse with ConfigParser
    config = configparser.ConfigParser()
    # keep the field names with the original case
    config.optionxform=str
    config.read_string(cfg)

    result = {}
    for section in config.sections():
        for k, v in config.items(section):
            result[k] = v
        # only one section is expected
        return section, result



def lambda_handler(event, context):
    prefix = event.get("pathParameters", {}).get("prefix", "")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    # get username from authorizer context
    requestContext = event.get('requestContext', {})
    logger.debug(requestContext)
    authorizer = requestContext.get('authorizer', {})
    logger.debug(authorizer)
    username = authorizer.get('username', {})

    base_prefix =  os.path.join(ROOT_PREFIX, username)
    full_prefix = os.path.join(base_prefix, prefix)

    # List objects
    s3_response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=full_prefix,
        Delimiter="/"
    )

    logger.debug(s3_response)

    folders = s3_response.get("CommonPrefixes", [])
    files = s3_response.get("Contents", [])

    # built the response
    api_response = {
        "prefix": prefix,
        "folders": {},
        "files": {}
    }

    file_metadata_dict = {}

    for folder in folders:
        folder_name = folder["Prefix"].split("/")[-2] + "/"  # trailing /
        link_prefix = folder["Prefix"]
        api_response["folders"][folder_name] = {
            "href": "/output-data/" + link_prefix
        }

    # Files
    for file_obj in files:
        key = file_obj["Key"]
        if key.endswith("/"):
            continue  # skip folder placeholders
        file_name = key.split("/")[-1]
        if file_name.endswith(".cfg"):
            # collect metadata
            try:
                response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
                file_content = response['Body'].read().decode('utf-8')
                file_key, metadata = cfg_to_json(file_content) # Decode for text files
                file_metadata_dict[file_key] = metadata
                print(file_content)
            except Exception as e:
                print(f"Error reading file from S3: {e}")
        else:
            # regular data file
            signed_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': key},
            #ExpiresIn=600
            )
            # TODO filter URL in HREF depending on user location
            api_response["files"][file_name] = {
             # keep them for later as stated in the above TODO
             # "s3_bucket": BUCKET_NAME,
             # "s3_key": key,
             "href": signed_url
            }

    logger.debug("metadata dicts %s", file_metadata_dict)
    logger.info("output response %s", api_response)
    # add metadata to file response
    for key, properties in file_metadata_dict.items():
        if key in api_response["files"]:
            api_response["files"][key]["properties"] = properties
        else:
            logger.warning("A cfg file %s.cfg is not associated to any data file", key)

    # get response format
    headers = event.get('headers', {})
    logger.debug("headers %s", headers)
    accept_header = headers.get('accept', "application/json")

    # Format the response
    if ("text/html" in accept_header):
        content_type = "text/html"
        formated_response = f"<h2>Listing for /{api_response["prefix"]}</h2>\n<ul>"
        for f_name, f_value in api_response["folders"].items():
            formated_response += f'<li><a href="{f_value["href"]}">{f_name}</a></li>'

        # Files
        for f_name, f_value in api_response["files"].items():
            formated_response += f'<li><a href="{f_value["href"]}">{f_name}</a></li>'

        formated_response += "</ul>"

    else:
        content_type = "application/json"
        formated_response = json.dumps(api_response)

    logger.debug("formatted response %s", formated_response)


    stage_variables = event.get('stageVariables', {})
    allow_origin_value = stage_variables.get('allowOrigin')
    logger.info("Allowed Origin is %s", allow_origin_value)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": content_type,
            "Access-Control-Allow-Origin": allow_origin_value,
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        },
        "body": formated_response
    }