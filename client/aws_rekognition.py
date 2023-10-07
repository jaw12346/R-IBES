import boto3
import os
from botocore.exceptions import NoCredentialsError

ACCESS_KEY = os.environ['S3-rekognition-demo-access']
SECRET_KEY = os.environ['S3-rekognition-demo-secret']
BUCKET_NAME = 'ir-hw2-proposal-09182023'


def detect_labels(file_name):
    """
    Method to take a file stored in S3 bucket `BUCKET_NAME` and send it through AWS Rekognition,
    returning facial recognition data from its celebrity database.

    :param file_name: Name of the file to scan in Rekognize stored in S3
    :type file_name: str
    :return: Tuple containing (Person's name, Match confidence, Facial feature mapping data)
             or False if an error occurred
    :rtype: Tuple(str, str, dict{str}) or bool
    """
    client = boto3.client('rekognition', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
                          region_name='us-east-2')

    try:
        response = client.recognize_celebrities(Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file_name}})
    except FileNotFoundError:
        print(f"The requested file \"{file_name}\" was not found in S3 bucket \"{BUCKET_NAME}\". "
              f"Unable to perform facial recognition procedure!")
        return False
    except NoCredentialsError:
        print("Unable to authenticate this session with AWS S3."
              "Unable to perform facial recognition procedure!")
        return False
    except Exception as e:
        print(f"Unknown exception occurred while attempting to perform facial recognition procedure : {e}")
        return False

    # Urls, Name, Id, Face, MatchConfidence, KnownGender
    # print(response)

    if len(response['CelebrityFaces']) > 0:
        retrieved_info = response['CelebrityFaces'][0]
        print(retrieved_info)
        if 'Name' in retrieved_info and 'MatchConfidence' in retrieved_info:
            name = retrieved_info['Name']
            match_confidence = retrieved_info['MatchConfidence']
            face = retrieved_info['Face']  # Facial mappings
            tup = (name, match_confidence, face)
            print((tup[0], tup[1]))
            return tup
    else:
        # AWS Rekognize was unable to match the image to a known celebrity
        return False
