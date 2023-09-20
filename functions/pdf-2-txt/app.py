import json
import unidecode
# from pdf_json_converter import convert_pdf_to_json
import importlib
converter_module = importlib.import_module("functions.pdf-2-text.pdf_json_converter")

import io
import boto3
import os
import time
from splunk_handler import force_flush
logging = importlib.import_module("functions.utils.wfn_logging")

wfn_logger = logging.wfn_logger
set_logger_context = logging.set_logger_context

import json
import os


s3 = boto3.resource('s3')

def lambda_handler(event, context):
    set_logger_context(wfn_logger, event, context)
    fn_name = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    start = time.time()
    
    wfn_logger.info(f"{fn_name}", extra={"PTR": "START"})
    wfn_logger.info("Received event: " + json.dumps(event, indent=2))
    
    data = json.loads(json.dumps(event))
    # wfn_logger.info("data: {}".format(data))
    
    BUCKET_NAME = data['bucket_name']
    KEY = data['key']
    DOC_ID = data['document_id']
    CLIENT_ID = "dummy" if 'client_id' not in data else data['client_id']
    KEY_DIR = DOC_ID if 'client_id' not in data else '{}/{}'.format(CLIENT_ID, DOC_ID)
    
    wfn_logger.info(f"bucket_name: {BUCKET_NAME}, key: {KEY}, client_id: {CLIENT_ID}, document_id: {DOC_ID}")
    wfn_logger.info("data: {}".format(data))

    pdf_2_json_path = "/tmp"
    name = KEY
    
    pdf_file = s3.Object(bucket_name=BUCKET_NAME, key=KEY).get()
    pdf_file_body = pdf_file['Body']
    pdf_file_stream = io.BytesIO(pdf_file_body.read())

    my_SOR = data['SOR'] if 'SOR' in data else None
    converter = converter_module.PDF2JSONConverter(BUCKET_NAME, None, SOR = my_SOR)
    final_result = converter.convert_pdf_to_json(pdf_file_stream, pdf_2_json_path, DOC_ID, KEY_DIR)

    parent_dir = os.environ['PARENT_DIR']
    if my_SOR is not None:
        parent_dir = f"{parent_dir}/{my_SOR}"

    key_output = '{}/{}/{}-txt.json'.format(parent_dir, KEY_DIR, DOC_ID)
    
    object = s3.Object(BUCKET_NAME,key_output)
    object.put(Body=json.dumps(final_result, indent=4))
    
    data = {}
    data['bucket_name'] = BUCKET_NAME
    data['key'] = KEY
    data['key_output'] = key_output
    data['document_id'] = DOC_ID
    data['client_id'] = CLIENT_ID

    num_pages = final_result['num_pages']
    
    pglvl = {}
    pglvl['bucket_name'] = BUCKET_NAME
    pglvl['keys'] = []
    for i in range(num_pages):
        entry = {}
        entry['pg_num'] = (i+1)
        entry['key'] = '{}/{}/{}-{}.txt'.format(parent_dir, KEY_DIR, str(DOC_ID), str(i+1).zfill(3))
        pglvl['keys'].append(entry)
    pglvl['document_id'] = DOC_ID
    pglvl['client_id'] = CLIENT_ID
    pglvl['SOR'] = my_SOR
    
    data['pglvl'] = pglvl
    
    wfn_logger.info(f"{fn_name}", extra={"PTR": "END", "Time": "%.2f" %((time.time()-start)*1000) })
    force_flush()
    
    return {
        'statusCode': 200,
        'body': data
    }
