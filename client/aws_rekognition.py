import os
import boto3
from botocore.exceptions import NoCredentialsError
from collections import namedtuple

ACCESS_KEY = os.environ['S3_rekognition_demo_access']
SECRET_KEY = os.environ['S3_rekognition_demo_secret']
BUCKET_NAME = 'ir-hw2-proposal-09182023'

awsPersonTup = namedtuple('awsPersonTup', ['name', 'match_confidence'])


def detect_labels(file_name, debug=False):
    """
    Method to take a file stored in S3 bucket `BUCKET_NAME` and send it through AWS Rekognition,
    returning facial recognition data from its celebrity database.

    :param file_name: Name of the file to scan in Rekognize stored in S3
    :type file_name: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: Tuple containing (Person's name, Match confidence, Facial feature mapping data)
             or False if an error occurred
    :rtype: awsPersonTup or bool
    """
    client = boto3.client('rekognition', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
                          region_name='us-east-2')

    try:
        response = client.recognize_celebrities(Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file_name}})
    except FileNotFoundError:
        if debug:
            print(f"The requested file \"{file_name}\" was not found in S3 bucket \"{BUCKET_NAME}\". "
                  f"Unable to perform facial recognition procedure!")
        return False
    except NoCredentialsError:
        if debug:
            print("Unable to authenticate this session with AWS S3."
                  "Unable to perform facial recognition procedure!")
        return False
    except Exception as unknown_exception:
        if debug:
            print(f"Unknown exception occurred while attempting to perform facial recognition procedure : "
                  f"{unknown_exception}")
        return False

    if len(response['CelebrityFaces']) > 0:
        retrieved_info = response['CelebrityFaces'][0]
        print(retrieved_info)
        if 'Name' in retrieved_info and 'MatchConfidence' in retrieved_info:
            name = retrieved_info['Name']
            match_confidence = retrieved_info['MatchConfidence']
            tup = awsPersonTup(name, match_confidence)
            if debug:
                print(tup.name, tup.match_confidence)
            return tup
    else:
        # AWS Rekognize was unable to match the image to a known celebrity
        return False
