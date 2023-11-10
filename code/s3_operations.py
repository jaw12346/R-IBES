"""
This file contains functions for uploading, downloading, and deleting files from an S3 bucket.
"""

import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


def get_env_vars():
    """
    Get the environment variables for the AWS S3 bucket.
    :return: S3 access key, S3 secret key, and S3 bucket name
    :rtype: str, str, str
    """
    access_key = os.environ['S3_rekognition_demo_access']
    secret_key = os.environ['S3_rekognition_demo_secret']
    bucket_name = 'ir-hw2-proposal-09182023'
    return access_key, secret_key, bucket_name


def get_file_from_user():
    """
    Get an image file from the user and check that it exists.

    :return: Path to the file
    :rtype: str
    """
    allowed_formats = ('.jpg', '.jpeg', '.png')
    while True:
        file_path = input('Enter the path to the face file you would like to search with: ')
        file_path = os.path.join(os.getcwd(), file_path)
        print(os.getcwd(), file_path)
        if not file_path.endswith(allowed_formats):
            print(f'Supported file types: {list(allowed_formats)}. Please try again!', end='\n\n')
            continue
        if os.path.exists(file_path):
            return file_path
        print(f'The file "{file_path}" does not exist. Please try again!', end='\n\n')


def upload_process(file_path, debug=False):
    """
    Get an image file from the user and upload it to S3.

    :param file_path: Path to the file to upload to S3
    :type file_path: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: File name on S3 or False if an error occurred
    :rtype: str or bool
    """
    file_name = file_path.split('\\')[-1]
    uploaded = upload_to_aws(file_path, file_name, debug=debug)
    if uploaded:
        return file_name
    return False


def upload_to_aws(local_file, s3_file, debug=False):
    """
    Upload a file to an S3 bucket.

    :param local_file: Path to the file to upload
    :type local_file: str
    :param s3_file: File name to use on S3
    :type s3_file: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: Success state of the upload -- True if successful, False otherwise
    :rtype: bool
    """
    access_key, secret_key, bucket_name = get_env_vars()
    s3_connection = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    try:
        s3_connection.upload_file(local_file, bucket_name, s3_file)
        if debug:
            print(f"Successfully uploaded \"{local_file}\" to S3 bucket \"{bucket_name}\".")
        return True
    except FileNotFoundError:
        if debug:
            print(f"The requested file \"{local_file}\" was not found. The file has likely been moved, renamed, "
                  f"or deleted.")
        return False
    except NoCredentialsError:
        if debug:
            print("Unable to authenticate this session with AWS S3.")
        return False
    except Exception as unknown_exception:
        if debug:
            print(f"Unknown exception occurred: {unknown_exception}")
        return False


def download_from_aws(file_name, debug=False):
    """
    Download a file from an S3 bucket.

    :param file_name: File name to download from S3
    :type file_name: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: Success state of the download -- True if successful, False otherwise
    :rtype: bool
    """
    access_key, secret_key, bucket_name = get_env_vars()
    s3_connection = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    try:
        temp_path = os.path.join(os.getcwd(), 'tmp')
        if not os.path.exists(temp_path):
            os.mkdir(temp_path)
        s3_connection.download_file(bucket_name, file_name, os.path.join(temp_path, file_name))
        if debug:
            print(f"Successfully downloaded \"{file_name}\" from S3 bucket \"{bucket_name}\"")
        return True
    except (FileNotFoundError, ClientError) as notfound_clienterr:
        if debug:
            print(f"The requested file \"{file_name}\" was not found in S3 bucket \"{bucket_name}\".")
            print(notfound_clienterr)
        return False
    except NoCredentialsError:
        if debug:
            print("Unable to authenticate this session with AWS S3.")
        return False
    except Exception as unknown_exception:
        if debug:
            print(f"Unknown exception occurred: {unknown_exception}")
        return False


def cleanup(file_name, debug=False):
    """
    Delete a file from an S3 bucket after it has been downloaded and is no longer needed online.

    :param file_name: Name of the file to delete from S3
    :type file_name: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: Success state of the deletion -- True if successful, False otherwise
    :rtype: bool
    """
    access_key, secret_key, bucket_name = get_env_vars()
    if isinstance(file_name, list):
        for file in file_name:
            cleanup(file)
    s3_connection = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    try:
        s3_connection.delete_object(Bucket=bucket_name, Key=file_name)
        if debug:
            print(f"Successfully deleted \"{file_name}\" from S3 bucket \"{bucket_name}\".")
        return True
    except FileNotFoundError:
        if debug:
            print(f"The requested file \"{file_name}\" was not found in S3 bucket \"{bucket_name}\".")
        return False
    except NoCredentialsError:
        if debug:
            print("Unable to authenticate this session with AWS S3.")
        return False
    except Exception as unknown_exception:
        if debug:
            print(f"Unknown exception occurred: {unknown_exception}")
        return False
