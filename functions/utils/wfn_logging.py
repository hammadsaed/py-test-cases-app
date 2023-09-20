import logging
from logging.config import dictConfig

from splunk_handler import SplunkHandler
from splunk_handler import force_flush

import json
import os

# Splunk settings
SPLUNK_HOST = os.getenv('SPLUNK_HOST', 'splunkcdlhec.es.ad.adp.com')
SPLUNK_PORT = int(os.getenv('SPLUNK_PORT', '80'))
SPLUNK_TOKEN = os.getenv('SPLUNK_TOKEN', 'wfnsplunkhecinput')
SPLUNK_INDEX = os.getenv('SPLUNK_INDEX', 'wfn_aws')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(created)f %(exc_info)s %(filename)s %(funcName)s %(levelname)s %(levelno)s %(lineno)d %(module)s %(message)s %(pathname)s %(process)s %(processName)s %(relativeCreated)d %(thread)s %(threadName)s'
        },
        'json-slim': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(filename)s %(funcName)s %(levelname)s %(lineno)d %(module)s %(message)s'
        }
    },
    'handlers': {
        'splunk': {
            'level': 'INFO',
            'class': 'splunk_handler.SplunkHandler',
            'formatter': 'json-slim',
            'host': SPLUNK_HOST,
            'port': SPLUNK_PORT,
            'token': SPLUNK_TOKEN,
            'index': SPLUNK_INDEX,
            'sourcetype': 'wfnlogs',
            'protocol': 'http',
            'debug': False
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'splunk'],
            'level': 'INFO'
        }
    }
}



def getWFNLogger(event, context):
    logger = getLogger()
    set_logger_context(logger, event, context)
    
    return logger


def getLogger():
    dictConfig(LOGGING)
    logger = logging.getLogger('')
    
    # OS env variables as part of log context
    params = {}
    params['DOMAIN'] = 'WFN-DT-BENEFITS'
    for p in ['AWS_LAMBDA_FUNCTION_NAME', 'AWS_LAMBDA_FUNCTION_VERSION', 'AWS_REGION', 'AWS_LAMBDA_LOG_GROUP_NAME', 'AWS_LAMBDA_LOG_STREAM_NAME']:
        params[p] = os.environ[p]
    adapter = CustomAdapter(logger, params)
    return adapter
    


def create_wfn_context(event):
    data = json.loads(json.dumps(event))
    
    client_id = data['client_id'] if 'client_id' in data else 'UNKNOWN'
    document_id = data['document_id'] if 'document_id' in data else 'UNKNOWN'
    
    wfn_context = {}
    wfn_context['client_id'] = client_id
    wfn_context['document_id'] = document_id
    
    return wfn_context

# def set_logger_context(logger, event, context):
    
#     params = {}
#     if context is not None:
#         params['AWS_REQUEST_ID'] = context.aws_request_id
    
#     wfn_context = create_wfn_context(event)
    
#     params['CLIENT_ID'] = wfn_context['client_id']
#     params['DOC_ID'] = wfn_context['document_id']
    
#     params.update(logger.extra)
#     logger.extra = params

def set_logger_context(logger, event, context):
    # print(f"PRE - logger.extra: {logger.extra}")

    params = logger.extra if logger.extra else {}
    if context is not None:
        params['AWS_REQUEST_ID'] = context['aws_request_id']
    
    wfn_context = create_wfn_context(event)
    params['CLIENT_ID'] = wfn_context['client_id']
    params['DOC_ID'] = wfn_context['document_id']
    
    logger.extra = params    
    # print(f"POST - logger.extra: {logger.extra}")

# Logging Adpater to add contextual information    
class CustomAdapter(logging.LoggerAdapter):
    
    def process(self, msg, kwargs):
        extras = kwargs['extra'] if 'extra' in kwargs else {}
        extras.update(self.extra)
        kwargs['extra']=extras
        return msg, kwargs

wfn_logger = getLogger()