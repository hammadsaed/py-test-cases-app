import pytest
import json
import importlib
import os
from unittest import mock
from wfn_logger_envs import wfn_logger_test_envs
import io

# Import the functions from pglvl-classifier.py
pglvl_classifier = importlib.import_module("functions.pglvl-classifier.main")

# Mock environment variables
os.environ['ENDPOINT_NAME'] = 'test-endpoint'
os.environ['API_GW_PAGE_CLASSIFIER_HOST'] = 'test-api-gw-host'
os.environ['API_GW_PAGE_CLASSIFIER_KEY'] = 'test-api-gw-key'
os.environ['PAGE_CLASSIFIER_MLOPS_ENABLED'] = 'False'


@pytest.fixture
def mock_s3_object():
    with mock.patch('boto3.resource') as mock_boto3_resource:
        mock_s3_resource = mock_boto3_resource.return_value
        mock_s3_object = mock_s3_resource.Object('test-bucket', 'test-key')
        mock_s3_object.get.return_value = {
            'Body': io.BytesIO(b'{"data": "test-data"}').read()
        }
        yield mock_s3_object


@pytest.fixture
def mock_runtime_invoke_endpoint():
    with mock.patch('boto3.client') as mock_boto3_client:
        mock_runtime = mock_boto3_client.return_value
        mock_runtime.invoke_endpoint.return_value = {
            'Body': io.BytesIO(b'{"plan_types": ["Medical"]}')
        }
        yield mock_runtime


def test_lambda_handler(mock_s3_object, mock_runtime_invoke_endpoint):
    event = {
        'bucket_name': 'test-bucket',
        'key': 'test-key',
        'pg_num': 123
    }
    context = {'aws_request_id': 'your_aws_request_id'}

    response = pglvl_classifier.lambda_handler(event, context)

    assert response['statusCode'] == 200
    assert response['body'] == {
        'pg_num': 123,
        'plan_type': 'Medical',
        'plan_types': ['Medical']
    }


def test_post_process():
    result = {
        "PlanA": 0.8,
        "PlanB": 0.6,
        "PlanC": 0.3
    }
    processed_result = pglvl_classifier.post_process(result)

    assert processed_result['plan_types'] == ['PlanA', 'PlanB', 'PlanC']
    assert len(processed_result['page_class_probabilities']) == 3


def test_get_result():
    labels = ['PlanA', 'PlanB', 'PlanC']
    result = {
        "PlanA": 0.8,
        "PlanB": 0.6,
        "PlanC": 0.3
    }
    processed_result = pglvl_classifier.get_result(labels, result)

    assert processed_result['plan_types'] == labels
    assert len(processed_result['page_class_probabilities']) == len(labels)

# Test cases for missing or invalid input values


def test_lambda_handler_missing_pg_num(mock_s3_object, mock_runtime_invoke_endpoint):
    event = {
        'bucket_name': 'test-bucket',
        'key': 'test-key'
    }
    context = {}

    response = pglvl_classifier.lambda_handler(event, context)

    assert response['statusCode'] == 200
    assert 'pg_num' not in response['body']


def test_post_process_empty_result():
    result = {}
    processed_result = pglvl_classifier.post_process(result)

    assert processed_result['plan_types'] == []
    assert len(processed_result['page_class_probabilities']) == 0


def test_get_result_empty_labels():
    labels = []
    result = {}
    processed_result = pglvl_classifier.get_result(labels, result)

    assert processed_result['plan_types'] == []
    assert len(processed_result['page_class_probabilities']) == 0


if __name__ == '__main__':
    pytest.main()
