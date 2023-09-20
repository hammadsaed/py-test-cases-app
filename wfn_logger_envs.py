import os


def set_env_variables_for_logger():
    os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'your_lambda_function_name'
    os.environ['AWS_LAMBDA_FUNCTION_VERSION'] = 'your_lambda_function_version'
    os.environ['AWS_REGION'] = 'your_aws_region'
    os.environ['AWS_LAMBDA_LOG_GROUP_NAME'] = 'your_lambda_log_group'
    os.environ['AWS_LAMBDA_LOG_STREAM_NAME'] = 'your_lambda_log_stream'

wfn_logger_test_envs = set_env_variables_for_logger()