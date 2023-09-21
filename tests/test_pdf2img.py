import io
import pytest
from unittest import mock
import importlib

from wfn_logger_envs import wfn_logger_test_envs

pdf2img = importlib.import_module("functions.pdf-2-img.app")

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
def set_environment_variables(monkeypatch):
    monkeypatch.setenv('AWS_LAMBDA_FUNCTION_NAME', 'your_lambda_function_name')
    monkeypatch.setenv('PARENT_DIR', 'your_parent_dir')
    monkeypatch.setenv('POPPLER_PATH', '/usr/local/Cellar/poppler/23.08.0/bin')


@pytest.fixture
def mock_s3_resources(mock_pdf_data):
    with mock.patch('boto3.resource') as mock_boto3_resource, \
         mock.patch('boto3.client') as mock_boto3_client, \
         mock.patch.object(pdf2img.s3, 'Object') as mock_s3_object:

        mock_s3_resource = mock.MagicMock()
        mock_s3_client = mock.MagicMock()

        mock_boto3_resource.return_value = mock_s3_resource
        mock_boto3_client.return_value = mock_s3_client

        mock_s3_object.return_value.get.return_value = {
        'Body': mock.MagicMock(read=mock.MagicMock(return_value=mock_pdf_data))}
    
        yield mock_s3_object, mock_boto3_resource, mock_boto3_client, mock_s3_resource, mock_s3_client


def assert_lambda_handler_result(result):
    assert result['statusCode'] == 200, "Expected 'statusCode' to be 200 in the result."
    body = result['body']

    assert 'bucket_name' in body, "Expected 'bucket_name' in the result body."
    assert 'key' in body, "Expected 'key' in the result body."
    assert 'document_id' in body, "Expected 'document_id' in the result body."

    assert 'tbl-detect' in body, "Expected 'tbl-detect' in the result body."
    tbl_detect = body['tbl-detect']

    assert 'bucket_name' in tbl_detect, "Expected 'bucket_name' in 'tbl-detect'."
    assert 'key' in tbl_detect, "Expected 'key' in 'tbl-detect'."
    assert 'document_id' in tbl_detect, "Expected 'document_id' in 'tbl-detect'."
    assert 'client_id' in tbl_detect, "Expected 'client_id' in 'tbl-detect'."
    assert 'SOR' in tbl_detect, "Expected 'SOR' in 'tbl-detect'."
    assert 'keys' in tbl_detect, "Expected 'keys' in 'tbl-detect'."

    keys = tbl_detect['keys']

    assert len(keys) > 0, "Expected 'keys' to be a non-empty list in 'tbl-detect'."

    for key_info in keys:
        assert 'img_key' in key_info, "Expected 'img_key' in a key_info dictionary."
        assert 'img_width' in key_info, "Expected 'img_width' in a key_info dictionary."
        assert 'img_height' in key_info, "Expected 'img_height' in a key_info dictionary."
        assert 'pg_num' in key_info, "Expected 'pg_num' in a key_info dictionary."


@pytest.fixture
def mock_pdf_data():
    # Load sample PDF data
    with open("sample.pdf", 'rb') as pdf_file:
        return pdf_file.read()


def test_lambda_handler(lambda_event, mock_s3_resources, mock_pdf_data, set_environment_variables): 
    mock_s3_resources
   

    image_contents = []
    for i, page in enumerate(pdf2img.convert_from_bytes(mock_pdf_data, dpi=300, fmt="png")):
        in_mem_file = io.BytesIO()
        page.save(in_mem_file, format="PNG")

        image_contents.append(in_mem_file.getvalue())

    result = pdf2img.lambda_handler(lambda_event, {"aws_request_id": "test_aws_request_id"})

    assert_lambda_handler_result(result)

    for i, image_content in enumerate(image_contents):
        # Save the image locally for inspection
        with open(f'page_{i + 1}.png', 'wb') as image_file:
                image_file.write(image_content)



# Run the test
if __name__ == '__main__':
    pytest.main()

