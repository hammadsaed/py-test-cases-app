import os
import pytest
from splunk_handler import force_flush

def set_mock_environment_variables():
    os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'your_lambda_function_name'
    os.environ['AWS_LAMBDA_FUNCTION_VERSION'] = 'your_lambda_function_version'
    os.environ['AWS_REGION'] = 'your_aws_region'
    os.environ['AWS_LAMBDA_LOG_GROUP_NAME'] = 'your_lambda_log_group'
    os.environ['AWS_LAMBDA_LOG_STREAM_NAME'] = 'your_lambda_log_stream'

def delete_mock_environment_variables():
    del os.environ['AWS_LAMBDA_FUNCTION_NAME']
    del os.environ['AWS_LAMBDA_FUNCTION_VERSION']
    del os.environ['AWS_REGION']
    del os.environ['AWS_LAMBDA_LOG_GROUP_NAME']
    del os.environ['AWS_LAMBDA_LOG_STREAM_NAME']


@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
    set_mock_environment_variables()
    yield
    force_flush()
    delete_mock_environment_variables()