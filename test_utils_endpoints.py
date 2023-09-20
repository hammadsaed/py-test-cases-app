import pytest
from unittest import mock
import importlib

from wfn_logger_envs import wfn_logger_test_envs
endpoints = importlib.import_module("functions.utils.endpoints_utils")

@pytest.fixture
def mock_sagemaker_runtime():
    with mock.patch('boto3.client') as mock_boto3_client:
        mock_runtime = mock_boto3_client.return_value
        mock_runtime.invoke_endpoint.return_value = {
            'StatusCode': 200,
            'Body': 'Mocked response data'
        }
        yield mock_runtime


@pytest.fixture
def mock_requests_post():
    with mock.patch('requests.request') as mock_post:
        yield mock_post


#Succes test cases for call_inference
def test_call_inference(mock_sagemaker_runtime):
    result = endpoints.call_inference('test-endpoint', 'test-payload')
    assert result['StatusCode'] == 200
    assert result['Body'] == 'Mocked response data'


#test cases for call_inference_api_gw
def test_call_inference_api_gw_success(mock_requests_post):
    mock_requests_post.return_value.status_code = 200
    mock_requests_post.return_value.content = '{"result": "success"}'

    result = endpoints.call_inference_api_gw(api_gw_host='test-host', api_gw_key='test-key', payload='test-payload')

    assert result == {"result": "success"}


# Test the failed scenario for call_inference_api_gw
def test_call_inference_api_gw_failure(mock_requests_post):
    mock_requests_post.side_effect = Exception("Mocked exception")

    with pytest.raises(Exception) as e:
        endpoints.call_inference_api_gw(api_gw_host='test-host', api_gw_key='test-key', payload='test-payload')

    assert str(e.value) == "Mocked exception"


#Test cases for call_inference_endpoint
def test_call_inference_endpoint_with_mlops_enabled_and_api_gw(mock_requests_post):
    mock_requests_post.return_value.status_code = 200
    mock_requests_post.return_value.content = '{"result": "success"}'

    result = endpoints.call_inference_endpoint(mlops_enabled=True, api_gw_host='test-host', api_gw_key='test-key', payload='test-payload')

    assert result == {"result": "success"}


def test_call_inference_endpoint_with_mlops_disabled_and_required_parameters(mock_sagemaker_runtime):
    mock_sagemaker_runtime.invoke_endpoint.return_value = {
        'StatusCode': 200,
        'Body': 'Mocked response data'
    }

    result = endpoints.call_inference_endpoint(mlops_enabled=False, endpoint_name='test-endpoint', payload='test-payload')

    assert result['StatusCode'] == 200
    assert result['Body'] == 'Mocked response data'

# Test when payload is missing (should raise a ValueError)
def test_call_inference_endpoint_missing_payload():
    with pytest.raises(ValueError) as e:
        endpoints.call_inference_endpoint(mlops_enabled=True, api_gw_host='test-host', api_gw_key='test-key')

    assert str(e.value) == 'Payload not provided.'


# Test when both api_gw_host and api_gw_key are missing (should raise a ValueError)
def test_call_inference_endpoint_missing_host_and_key():
    with pytest.raises(ValueError) as e:
        endpoints.call_inference_endpoint(mlops_enabled=True, payload='test-payload')

    assert str(e.value) == 'Host api missing.'


# Test when endpoint_name is missing (should raise a ValueError)
def test_call_inference_endpoint_missing_endpoint_name():
    with pytest.raises(ValueError) as e:
        endpoints.call_inference_endpoint(mlops_enabled=False, payload='test-payload')

    assert str(e.value) == 'EndpointName missing.'


if __name__ == '__main__':
    pytest.main()
