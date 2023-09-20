import json
import requests
import io
import boto3
from PIL import Image
import tempfile
import os
import time
import importlib
from pdf2image import convert_from_path, convert_from_bytes, pdfinfo_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)

from splunk_handler import force_flush

logging = importlib.import_module("functions.utils.wfn_logging")

wfn_logger = logging.wfn_logger
set_logger_context = logging.set_logger_context

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    set_logger_context(wfn_logger, event, context)
    fn_name = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    start = time.time()

    wfn_logger.info(f"{fn_name}", extra={"PTR": "START"})
    wfn_logger.info("Received event: " + json.dumps(event, indent=2))

    data = json.loads(json.dumps(event))
    wfn_logger.info("data: {}".format(data))
    BUCKET_NAME = data['bucket_name']
    KEY = data['key']
    DOC_ID = data['document_id']
    CLIENT_ID = "dummy" if 'client_id' not in data else data['client_id']
    KEY_DIR = DOC_ID if 'client_id' not in data else '{}/{}'.format(
        CLIENT_ID, DOC_ID)
    my_SOR = data['SOR'] if 'SOR' in data else None
    pdf_file = s3.Object(bucket_name=BUCKET_NAME, key=KEY).get()
    pdf_file_body = pdf_file['Body']

    POPPLER_PATH = '/opt/bin'
    with tempfile.TemporaryDirectory() as path:
        images = convert_from_bytes(
            pdf_file_body.read(), dpi=300, fmt="png", output_folder=path)

    output = {}
    output['bucket_name'] = BUCKET_NAME
    output['key'] = KEY
    output['document_id'] = DOC_ID

    parent_dir = os.environ['PARENT_DIR']
    if my_SOR is not None:
        parent_dir = f"{parent_dir}/{my_SOR}"

    keys = []
    for i, image in enumerate(images, start=1):
        wfn_logger.info("image type: {}".format(image))
        wfn_logger.info("image size: {}".format(image.size))
        in_mem_file = io.BytesIO()
        image.save(in_mem_file, format="PNG")

        key_output = '{}/{}/{}-{}.png'.format(parent_dir,
                                              KEY_DIR, DOC_ID, str(i).zfill(3))

        object = s3.Object(BUCKET_NAME, key_output)
        object.put(Body=in_mem_file.getvalue())

        img_output = {}
        img_output['img_key'] = key_output
        img_output['img_width'] = image.size[0]
        img_output['img_height'] = image.size[1]
        img_output['pg_num'] = i
        img_output['document_id'] = DOC_ID
        img_output['client_id'] = CLIENT_ID
        img_output['SOR'] = my_SOR

        keys.append(img_output)

        tbl_detect = {}
        tbl_detect['bucket_name'] = BUCKET_NAME
        tbl_detect['key'] = KEY
        tbl_detect['document_id'] = DOC_ID
        tbl_detect['client_id'] = CLIENT_ID
        tbl_detect['keys'] = keys
        tbl_detect['SOR'] = my_SOR

        output['tbl-detect'] = tbl_detect

    wfn_logger.info(f"{fn_name}", extra={"PTR": "END",
                    "Time": "%.2f" % ((time.time()-start)*1000)})
    force_flush()

    return {
        "statusCode": 200,
        "body": output
    }
