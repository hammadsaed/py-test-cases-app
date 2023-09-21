import json
import sys
import pickle
import os
import boto3
import io
import time

from splunk_handler import force_flush
from wfn_logging import wfn_logger, set_logger_context
from endpoints_utils import call_inference_api_gw

API_GW_PAGE_CLASSIFIER_HOST = os.getenv('API_GW_PAGE_CLASSIFIER_HOST', None)
API_GW_PAGE_CLASSIFIER_KEY = os.getenv('API_GW_PAGE_CLASSIFIER_KEY', None)
PAGE_CLASSIFIER_MLOPS_ENABLED = os.getenv(
    'PAGE_CLASSIFIER_MLOPS_ENABLED', 'False') == 'True'
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
# ['Dental','LifeADD','LTD','Medical','Other','STD','Vision']
# THRESH = [.5,.5,.5,.5,.5,.5,.5] #UPDATE TO INDEX THRESHOLD
THRESH = 0.5


def invocationConfig(endpointName, contentType, payload):

    useMCEndpoint = "true" == os.getenv('MC_SCIKIT_ENDPOINT_ENABLED')
    MC_SCIKIT_ENDPOINT_NAME = os.getenv('MC_SCIKIT_ENDPOINT_NAME')
    MC_SCIKIT_ENDPOINT_HOSTNAME = os.getenv('MC_SCIKIT_ENDPOINT_HOSTNAME')

    endpointInvocationConfig = {}
    endpointInvocationConfig['EndpointName'] = MC_SCIKIT_ENDPOINT_NAME if useMCEndpoint else endpointName
    endpointInvocationConfig['ContentType'] = contentType
    endpointInvocationConfig['Body'] = payload

    if useMCEndpoint:
        endpointInvocationConfig['TargetContainerHostname'] = MC_SCIKIT_ENDPOINT_HOSTNAME

    wfn_logger.info(f"Invocation config: {endpointInvocationConfig}")

    return endpointInvocationConfig


# comment to trigger build - 04.02.2021
def lambda_handler(event, context):
    set_logger_context(wfn_logger, event, context)
    fn_name = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    start = time.time()
    wfn_logger.info(f"{fn_name}", extra={"PTR": "START"})

    s3 = boto3.resource('s3')
    runtime = boto3.client('runtime.sagemaker')

    wfn_logger.info("Received event: " + json.dumps(event, indent=2))
    data = json.loads(json.dumps(event))

    BUCKET_NAME = data['bucket_name']
    KEY = data['key']

    PG_NUM = None
    if 'pg_num' in data:
        PG_NUM = data['pg_num']

    obj_file = s3.Object(bucket_name=BUCKET_NAME, key=KEY)
    payload = obj_file.get()['Body'].read().decode()

    # invoke sagemaker endpoint
    if not PAGE_CLASSIFIER_MLOPS_ENABLED:
        response = runtime.invoke_endpoint(
            **invocationConfig(ENDPOINT_NAME, 'application/json', json.dumps({'data': payload})))
        result = json.loads(response['Body'].read())
    else:
        result = call_inference_api_gw(API_GW_PAGE_CLASSIFIER_HOST, API_GW_PAGE_CLASSIFIER_KEY,
                                       json.dumps({'data': payload}))

    # post_process(result)
    output = post_process(result)

    wfn_logger.info('output: {}'.format(output))

    response = {}

    if PG_NUM is not None:
        response['pg_num'] = PG_NUM

    plan_types = output['plan_types']

    # TODO: VJOSHI - handle multiple plan types, once downstream is ready!
    # in case of more than one plan types, selecting 1st one
    response['plan_type'] = plan_types[0]
    response['plan_types'] = plan_types

    wfn_logger.info(f"{fn_name}", extra={"PTR": "END",
                    "Time": "%.2f" % ((time.time()-start)*1000)})
    force_flush()
    return {
        'statusCode': 200,
        'body': response
    }


def post_process(result):
    wfn_logger.info("original: {}".format(result))
    res = []
    res.append([val for (key, val) in result.items()])
    wfn_logger.info("res[0]: {}".format(res[0]))
    Class = [key for (key, val) in result.items()]

    wfn_logger.info("prob: {}".format(res[0]))

    zipped = result
    # Big = max(res[0])
    # define threshhold
    labels = []
    thresh = THRESH
    if max(res[0]) >= thresh:
        for i in range(len(res[0])):
            if res[0][i] >= thresh:  # [i]: #--- Use index if thresh per plan type
                # if res[0][i]>=thresh*Big:
                if not labels:
                    labels.append(Class[i])
                else:
                    j = 0
                    while j < len(labels) and zipped[Class[i]] < zipped[labels[j]]:
                        j += 1
                    labels.insert(j, Class[i])
    else:
        labels.append(Class[res[0].index(max(res[0]))])

    final_result = get_result(labels, zipped)
    wfn_logger.info(final_result)
    return final_result


def get_result(labels, zipped):
    result = {}
    result['plan_types'] = labels
    res2 = []
    for k in zipped:
        res2.append({'label': k, 'probability': zipped[k]})

    result['page_class_probabilities'] = res2

    return result
