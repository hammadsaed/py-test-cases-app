# from unittest.mock import Mock
# import base64
# import pytest
# from PIL import Image
# from io import BytesIO
# import json
# import os
# import importlib
# from moto import mock_s3
# import boto3
# from botocore.stub import Stubber
# # Import your lambda_handler function from pdf2img module
# pdf2img = importlib.import_module("pdf-script.pdf2img")


# @pytest.fixture
# def sample_pdf():
#     pdf_file_path = 'sample.pdf'

#     with open(pdf_file_path, 'rb') as pdf_file:
#         pdf_content = pdf_file.read()

#     return BytesIO(pdf_content)


# @pytest.fixture
# def lambda_event(sample_pdf):
#     pdf_content_base64 = base64.b64encode(sample_pdf.read()).decode('utf-8')
#     event = {
#         'bucket_name': 'your_bucket_name',
#         'key': 'your_pdf_key.pdf',
#         'document_id': 'your_document_id',
#         'client_id': 'your_client_id',
#         'pdf_file_body_base64': pdf_content_base64,
#     }

#     return event


# @mock_s3
# def test_lambda_handler(mocker, lambda_event):
#     os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'your_lambda_function_name'
#     os.environ['PARENT_DIR'] = 'your_parent_cdir'
#     s3_client = boto3.client('s3')
#     s3_stubber = Stubber(s3_client)

#     # Define the expected S3 operations and their responses
#     expected_params = {
#         'Bucket': 'your_bucket_name',
#         'Key': 'your_pdf_key.pdf'
#     }
#     s3_stubber.add_response(
#         'get_object', {'Body': BytesIO(b'fake_pdf_content')}, expected_params)

#     # Mock the pdf2image.convert_from_bytes function to return a fake image
#     mocker.patch('pdf2image.convert_from_bytes',
#                  return_value=[Image.new('RGB', (100, 100))])

#     # Start the Stubber
#     with s3_stubber:
#         # Call your Lambda handler function with the sample event
#         result = pdf2img.lambda_handler(lambda_event, None)

#     # Verify that the Lambda function returns a valid response
    # assert 'statusCode' in result
    # assert result['statusCode'] == 200

    # # Verify that the Lambda function output contains the expected keys
    # assert 'bucket_name' in result['body']
    # assert 'key' in result['body']
    # assert 'document_id' in result['body']

    # # Verify that images were generated and saved in S3
    # assert 'tbl-detect' in result['body']
    # keys = result['body']['tbl-detect']['keys']
    # assert len(keys) > 0

    # # Optionally, you can further verify the generated images
    # for key_info in keys:
    #     assert 'img_key' in key_info
    #     assert 'img_width' in key_info
    #     assert 'img_height' in key_info
    #     assert 'pg_num' in key_info

#         # Here, you can add assertions to check S3 operations (e.g., key_info['img_key'])
#         # and image properties (e.g., key_info['img_width'], key_info['img_height'])


# # Run the tests
# if __name__ == '__main__':
#     pytest.main()


# import json
# import os
# import tempfile
# import io
# import boto3
# from unittest import mock
# import pytest
# from PIL import Image
# from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError

# # Import your lambda_handler function from the source file
# import importlib
# script = importlib.import_module("pdf-script.pdf2img")

# # Define mock S3 client


# @mock.patch('boto3.client')
# def test_lambda_handler(mock_s3_client):
#     # Mock S3 resource
#     mock_s3 = mock_s3_client.return_value
#     mock_s3.Object.return_value.get.return_value = {
#         'Body': io.BytesIO(b'your_mocked_pdf_content')
#     }

#     # Define a test event with mock values
#     test_event = {
#         'bucket_name': 'mocked_bucket',
#         'key': 'mocked_key.pdf',
#         'document_id': 'mocked_document_id',
#         'client_id': 'mocked_client_id',
#         'SOR': 'mocked_SOR'
#     }

#     # Set necessary environment variables
#     os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'your_function_name'
#     os.environ['PARENT_DIR'] = 'your_parent_dir'

#     # Call the lambda_handler function with the mock test event
#     result = script.lambda_handler(test_event, None)

#     # Assertions for the result
#     assert result['statusCode'] == 200

#     # Check the contents of the output
#     output = result['body']

#     # Add more assertions based on your expected output
#     assert 'bucket_name' in output
#     assert 'key' in output
#     assert 'document_id' in output

#     # You can add more assertions to validate the output structure and content here


# # Run the test
# if __name__ == '__main__':
#     pytest.main()