"""
This file contains the methods to handle user contributions to the local facial recognition database.
"""

from code import local_facial_recognition as lfr
from code import conversions


def get_user_contributed_name():
    """
    Method to request a name from the user to save to the local facial recognition database in case AWS Rekognize was
    unable to match their provided image to a known celebrity.

    :return: Full name (first last) of the person in the user-provided photo.
    :rtype: str
    """
    print("\nThank you for offering to contribute to this IR system!")
    while True:
        name = input("Please enter the name (first, last) of the person in this image: ")
        if ', ' not in name:
            print("Unable to parse your input. Please make sure you provide the name in the format: "
                  "FIRST NAME, COMMA, SPACE, LAST NAME\n")
        else:
            split = name.split(', ')
            first_name = split[0]
            last_name = split[1]
            if first_name is None:
                print("Unable to parse first name. Returned as \"\".\n")
                continue
            if last_name is None:
                print("Unable to parse last name. Returned as \"\".\n")
                continue
            name = f'{first_name} {last_name}'
            return name


def contribute(file_location, upload_encoding):
    """
    Method to add a user-provided image to the local facial recognition database.

    :param file_location: Local location of the file to add to the local db
    :type file_location: str
    :param upload_encoding: Pre-computed encoding of the image to add to the local db
    :type upload_encoding: ndarray(128,)
    :return: Result of the addition to the local db (True if successful, False otherwise) AND the name of the person
    :rtype: bool, str
    """
    provided_name = get_user_contributed_name().title()
    normalized_name = conversions.get_normalized_name(provided_name)
    person_dir = lfr.get_person_directory(normalized_name)
    if person_dir:
        # Duplicate name!
        print(f"The name <{provided_name}> already exists in the database but doesn't match the face "
              f"you provided.")
        print('R-IBES does not support the usage of duplicate name entries, '
              'so we cannot complete your query.')
        return False, ''

    # No one with this name and face exists in the DB
    print(f"Adding <{provided_name}> to the local DB...")
    result = lfr.add_to_db(file_location, upload_encoding, normalized_name)
    return result, provided_name


def ask_contribute(file_path):
    """
    Method to ask the user if they would like to contribute to the local facial recognition database.

    :param file_path: Path of the file the user provided.
    :type file_path: str
    :return: Whether the user consents to contributing to the local db.
    :rtype: bool
    """
    print(f"AWS Rekognize was unable to recognize the face provided in \"{file_path}\"")
    while True:
        response = (input("Would you like to contribute to this IR system by providing this person's name? (y/n): ")
                    .lower().strip())
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            # End program
            return False
        print("Unable to interpret your response...")
        continue
