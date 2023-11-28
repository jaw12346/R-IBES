"""
Main module for the R-IBES client.
"""

import os
import random
import sys

from PIL import Image
from numpy import array_equal

from src import local_facial_recognition as lfr
from src import entity_search as es
from src import conversions

from src import aws_rekognition
from src import user_contribution
from src import s3_operations


def local_search(search_file_location, debug=False):
    """
    Search for a person using the local facial recognition database.

    :param search_file_location: Local location of the file to search for using the local db
    :type search_file_location: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: Name of the person or 'UNKNOWN' if the image doesn't match anyone in the local db
    """
    test_encoding = lfr.generate_face_encoding(search_file_location, debug=debug)
    most_likely_person = lfr.identify_person_from_encoding(test_encoding, debug=debug)
    return most_likely_person, test_encoding


def aws_search(search_file_location, debug=False):
    """
    Search for a person using AWS Rekognition.

    :param search_file_location: Local location of the file to search for using AWS
    :type search_file_location: str
    :param debug: Enable debug mode
    :type debug: bool
    :return: AWS-detected person name or False if no person was detected
    :rtype: AWSPersonTup or bool
    """
    s3_file_name = s3_operations.upload_process(search_file_location, debug=debug)

    if s3_file_name:
        detected_celebrity = aws_rekognition.detect_labels(s3_file_name, debug=debug)
        if detected_celebrity:
            s3_operations.cleanup(s3_file_name, debug=debug)
            return detected_celebrity
        print("No celebrity detected by AWS.")
        s3_operations.cleanup(s3_file_name, debug=debug)
        return False
    print("Unable to upload file to AWS S3.")
    return False


def user_query():
    """
    Gather the user's query from the command line.

    :return: A list where each element is an independent query string.
             Each query string is a space-separated list of terms.
    :rtype: list(str)
    """
    while True:
        query = input("Enter a question in the form '<biographical_term> <biographical_term> ...'\n"
                      "Example intention: "
                      "'What is the area code of each of George H. W. Bush's children's birthplaces?'\n"
                      "Example query: 'child birthPlace areaCode'\n")
        if len(query.split(' ')) < 1:
            # Query must consist of (at least) an entity and a biographical term
            print("Invalid query. Please try again.")
            continue
        return query.split(' AND ')


def random_person_image(directory):
    """
    Get a random image from the directory.

    :param directory: Directory to get the image from
    :type directory: str
    :return: Path to the image
    :rtype: str
    """
    cwd = os.getcwd()
    directory = directory.split('./')[-1]
    images = os.listdir(directory)
    return f'{directory}/{random.choice(images)}'


def main():
    """
    Main method for the R-IBES client.
    `python3 main.py [--offline] [--debug]`
    """
    # Determine if we are running in offline mode or debug mode from the command line
    offline = False
    debug = False
    if '--offline' in sys.argv:
        print('Running in offline mode.')
        offline = True
    if '--debug' in sys.argv:
        print('Running in debug mode.')
        debug = True

    # Gather the image and the query from the user
    search_file_location = s3_operations.get_file_from_user()
    queries = user_query()

    # First attempt to query the local DB, reducing our reliance on AWS
    most_likely_person, search_encoding = local_search(search_file_location, debug)
    normalized_name = ''

    # Image matched a person in the local db
    if most_likely_person != 'UNKNOWN PERSON':
        print('Match detected in local DB!')

        # Determine if this exact image already exists in the DB
        duplicate_image = False

        # Collect all encodings of the person in the DB
        existing_encodings = lfr.get_person_db_encodings(most_likely_person, debug)

        # Compare the search encoding to each encoding of the person in the DB
        for existing_encoding in existing_encodings:
            # Compare the search encoding to the existing encoding
            # If the search encoding is a match, we have a duplicate image
            # If the search encoding is not a match, we have a new image of the same person
            if array_equal(search_encoding, existing_encoding):
                # The image the user provided already exists in the DB
                print('Duplicate image detected in local DB! Continuing without adding to DB.')
                duplicate_image = True
                normalized_name = most_likely_person
                break

        if not duplicate_image:
            # Save this new image to the DB
            print('Unique image of a known person provided. Adding to local DB for future use!')
            lfr.add_to_db(search_file_location, search_encoding, most_likely_person)
            normalized_name = most_likely_person

    # If the face doesn't match any known person in the local DB, attempt to detect person using AWS Rekognition
    # This conditional is only entered if online mode is active (S3 keys are required for AWS Rekognition)
    elif most_likely_person == 'UNKNOWN PERSON' and not offline:
        aws_detected = aws_search(search_file_location, debug)
        if isinstance(aws_detected, aws_rekognition.AWSPersonTup):
            normalized_name = conversions.get_normalized_name(aws_detected.name)
            # AWS matched the person but local db did not
            print(f'AWS successfully detected a known person <{aws_detected.name}> in the image!')
            print('Scanning local DB...')
            person_dir = lfr.get_person_directory(normalized_name)
            if person_dir:
                print(f"The name <{aws_detected.name}> already exists in the database but doesn't match the face "
                      f"you provided.")

                random_img_path = random_person_image(person_dir)
                img = Image.open(random_img_path)
                img.show()

                while True:
                    response = input('Is this the same person? (y/n): ').lower().strip()
                    if response in ('y', 'yes'):
                        if aws_detected.match_confidence > 0.9:
                            lfr.add_to_db(search_file_location, search_encoding, normalized_name)
                            print(f'Added image to <{normalized_name}>. Continuing with query...')
                        else:
                            print('AWS confidence was too low to add to local DB. Continuing with query...')
                        break
                    if response in ('n', 'no'):
                        # End program
                        print('R-IBES does not support the usage of duplicate name entries, '
                              'so we cannot complete your query.')
                        return
                    else:
                        print('Invalid response. Please try again.')
                        continue

        else:
            # AWS does not recognize the person (or in offline mode) and the face doesn't match anyone in the local DB
            contribute_proceed = user_contribution.ask_contribute(search_file_location)
            if not contribute_proceed:
                # User did not want to contribute to the DB or the upload failed
                # End the program
                print('Thank you for using R-IBES. Goodbye!')
                return
            if contribute_proceed:
                result, name = user_contribution.contribute(search_file_location, search_encoding)
                if not result:
                    return
                print('Successfully added to local DB!')
                normalized_name = conversions.get_normalized_name(name)

    for query in queries:
        # Handle multiple queries
        es.main(query, normalized_name, debug)

    print('Thank you for using R-IBES. Goodbye!')


if __name__ == '__main__':
    main()
