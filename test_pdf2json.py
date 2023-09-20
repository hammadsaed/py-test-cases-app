import json
import io
import pytest
from unittest import mock
import importlib

from wfn_logger_envs import wfn_logger_test_envs

converter_module = importlib.import_module("functions.pdf-2-txt.pdf_json_converter")
pdf2json = importlib.import_module("functions.pdf-2-txt.app")


@pytest.fixture
def lambda_event():
    # Define a sample Lambda event
    return {
        "bucket_name": "my_bucket",
        "key": "my_key",
        "document_id": "12345",
        "client_id": "dummy",
        "SOR": "sor_value"
    }


@pytest.fixture
def mock_pdf_data():
    # Load sample PDF data
    with open("sample.pdf", 'rb') as pdf_file:
        return pdf_file.read()


@pytest.fixture
def mock_s3_resources(mock_pdf_data):
    with mock.patch('boto3.resource') as mock_boto3_resource, \
        mock.patch.object(pdf2json.s3, 'Object') as mock_s3_object, \
        mock.patch.object(converter_module.s3, 'Object') as mock_s3_converter_object:

        mock_s3_resource = mock.MagicMock()
        mock_boto3_resource.return_value = mock_s3_resource

        mock_s3_object.return_value.get.return_value = {
        'Body': mock.MagicMock(read=mock.MagicMock(return_value=mock_pdf_data))}
    
        mock_s3_converter_object.return_value.get.return_value = {
        'Body': mock.MagicMock(read=mock.MagicMock(return_value=mock_pdf_data))}

        yield mock_s3_object, mock_s3_resource, mock_s3_converter_object


@pytest.fixture
def set_environment_variables(monkeypatch):
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_NAME', 'your_lambda_function_name')
    monkeypatch.setenv('PARENT_DIR', 'your_parent_dir')


def assert_lambda_handler_result(result):
    assert result['statusCode'] == 200, "Expected 'statusCode' to be 200 in the result."

    body = result['body']
    assert 'bucket_name' in body, "Expected 'bucket_name' in the result body."
    assert 'key' in body, "Expected 'key' in the result body."
    assert 'document_id' in body, "Expected 'document_id' in the result body."
    assert 'key_output' in body, "Expected 'key_output' in the result body."
    assert 'pglvl' in body, "Expected 'pglvl' in the result body."

    keys = body['pglvl']['keys']
    assert len(keys) > 0
    for key_info in keys:
        assert 'pg_num' in key_info,  "Expected 'pg_num' in the key_info dictionary."
        assert 'key' in key_info,  "Expected 'key' in the key_info dictionary."


def test_lambda_handler(lambda_event, mock_pdf_data, mock_s3_resources, set_environment_variables):
    mock_s3_resources

    # Create the PDF2JSONConverter instance
    converter = converter_module.PDF2JSONConverter(lambda_event['bucket_name'], None, SOR=lambda_event['SOR'])

    pdf_file_stream = io.BytesIO(mock_pdf_data)
    json_to_write = converter.convert_pdf_to_json(pdf_file_stream, "/tmp", lambda_event['document_id'],
                                                  '{}/{}'.format(lambda_event['client_id'], lambda_event['document_id']))

    result = pdf2json.lambda_handler(lambda_event,  {"aws_request_id": "test_aws_request_id"})

    assert_lambda_handler_result(result)
    # Save the generated JSON locally for inspection
    with open("pdf_to_text.json", 'w') as json_file:
        json.dump(json_to_write, json_file)


if __name__ == '__main__':
    pytest.main()