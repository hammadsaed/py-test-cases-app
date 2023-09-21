import boto3
import json
import os
import io
import requests
import importlib
logging = importlib.import_module("functions.utils.wfn_logging")

s3 = boto3.resource('s3')


def call_inference(endpoint_name, payload, content_type='application/json'):
    runtime = boto3.client('runtime.sagemaker')
    response = runtime.invoke_endpoint(EndpointName=endpoint_name,
                                       ContentType=content_type,
                                       Body=payload)
    return response


def call_inference_api_gw(api_gw_host, api_gw_key, payload):
    api_gw_endpoint = f'https://{api_gw_host}/prod/single'
    api_gw_headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_gw_key
    }

    try:
        response = requests.request('POST',
                                    api_gw_endpoint,
                                    headers=api_gw_headers,
                                    data=payload)
        response.raise_for_status()
        result = json.loads(response.content)

        if isinstance(result, dict):
            if 'ErrorCode' in result:
                raise ValueError(result)
    except Exception as e:
        logging.wfn_logger.error(f'Exception calling API GW: {e}')
        raise e

    return result


def call_inference_endpoint(**kwargs):

    if "mlops_enabled" in kwargs:
        mlops_enabled = kwargs.get('mlops_enabled')
    else:
        mlops_enabled = True

    if kwargs.get('payload'):
        payload = kwargs.get('payload')
    else:
        raise ValueError('Payload not provided.')

    if mlops_enabled:
        if kwargs.get('api_gw_host'):
            api_gw_host = kwargs.get('api_gw_host')
        else:
            raise ValueError('Host api missing.')

        if kwargs.get('api_gw_key'):
            api_gw_key = kwargs.get('api_gw_key')
        else:
            raise ValueError('Host api key missing.')

        return call_inference_api_gw(api_gw_host, api_gw_key, payload)

    if kwargs.get('endpoint_name'):
        endpoint_name = kwargs.get('endpoint_name')
    else:
        raise ValueError('EndpointName missing.')

    if kwargs.get('content_type'):
        content_type = kwargs.get('content_type')
    else:
        content_type = 'application/json'

    return call_inference(endpoint_name, payload, content_type=content_type)
