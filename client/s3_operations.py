import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


ACCESS_KEY = os.environ['S3-rekognition-demo-access']
SECRET_KEY = os.environ['S3-rekognition-demo-secret']
BUCKET_NAME = 'ir-hw2-proposal-09182023'


def get_file_from_user():
    """
    Get an image file from the user and check that it exists.

    :return: Path to the file
    :rtype: str
    """
    allowed_formats = ('.jpg', '.jpeg', '.png')
    while True:
        file_path = input('Enter the path to the file you would like to upload to S3: ')
        if not file_path.endswith(allowed_formats):
            print(f'Supported file types: {list(allowed_formats)}. Please try again!\n')
            continue
        if os.path.exists(file_path):
            return file_path


def upload_process():
    """
    Get an image file from the user and upload it to S3.

    :return: File name on S3
    :rtype: str
    """
    while True:
        file_path = get_file_from_user()
        file_name = file_path.split('\\')[-1]
        uploaded = upload_to_aws(file_path, file_name)
        if uploaded:
            return file_name


def upload_to_aws(local_file, s3_file):
    """
    Upload a file to an S3 bucket.

    :param local_file: Path to the file to upload
    :type local_file: str
    :param s3_file: File name to use on S3
    :type s3_file: str
    :return: Success state of the upload -- True if successful, False otherwise
    :rtype: bool
    """
    s3_connection = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    try:
        s3_connection.upload_file(local_file, BUCKET_NAME, s3_file)
        print(f"Successfully uploaded \"{local_file}\" to S3 bucket \"{BUCKET_NAME}\".")
        return True
    except FileNotFoundError:
        print(f"The requested file \"{local_file}\" was not found. The file has likely been moved, renamed, "
              f"or deleted.")
        return False
    except NoCredentialsError:
        print("Unable to authenticate this session with AWS S3.")
        return False
    except Exception as unknown_exception:
        print(f"Unknown exception occurred: {unknown_exception}")
        return False


def download_from_aws(file_name):
    """
    Download a file from an S3 bucket.

    :param file_name: File name to download from S3
    :type file_name: str
    :return: Success state of the download -- True if successful, False otherwise
    :rtype: bool
    """
    s3_connection = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    try:
        temp_path = os.path.join(os.getcwd(), 'tmp')
        if not os.path.exists(temp_path):
            os.mkdir(temp_path)
        s3_connection.download_file(BUCKET_NAME, file_name, os.path.join(temp_path, file_name))
        print(f"Successfully downloaded \"{file_name}\" from S3 bucket \"{BUCKET_NAME}\"")
        return True
    except (FileNotFoundError, ClientError) as notfound_clienterr:
        print(f"The requested file \"{file_name}\" was not found in S3 bucket \"{BUCKET_NAME}\".")
        print(notfound_clienterr)
        return False
    except NoCredentialsError:
        print("Unable to authenticate this session with AWS S3.")
        return False
    except Exception as unknown_exception:
        print(f"Unknown exception occurred: {unknown_exception}")
        return False


def cleanup(file_name):
    """
    Delete a file from an S3 bucket after it has been downloaded and is no longer needed online.

    :param file_name: Name of the file to delete from S3
    :type file_name: str
    :return: Success state of the deletion -- True if successful, False otherwise
    :rtype: bool
    """
    if isinstance(file_name, list):
        for file in file_name:
            cleanup(file)
    s3_connection = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    try:
        s3_connection.delete_object(Bucket=BUCKET_NAME, Key=file_name)
        print(f"Successfully deleted \"{file_name}\" from S3 bucket \"{BUCKET_NAME}\".")
        return True
    except FileNotFoundError:
        print(f"The requested file \"{file_name}\" was not found in S3 bucket \"{BUCKET_NAME}\".")
        return False
    except NoCredentialsError:
        print("Unable to authenticate this session with AWS S3.")
        return False
    except Exception as unknown_exception:
        print(f"Unknown exception occurred: {unknown_exception}")
        return False
