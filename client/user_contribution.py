def get_user_contributed_name():
    """
    Method to request a name from the user to save to the local facial recognition database in case AWS Rekognize was
    unable to match their provided image to a known celebrity.

    :return: First Name, Last name of the person in the user-provided photo.
    :rtype: str, str
    """
    print("\nThank you for offering to contribute to this IR system!")
    while True:
        name = input("Please enter the name (first, last) of the person in this image: ")
        if ', ' not in name:
            print("Unable to parse your input. Please make sure you provide the name in the format: "
                  "FIRST NAME, COMMA, SPACE, LAST NAME\n")
            continue
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
            return first_name, last_name


def user_contribution(file_name):
    first_name, last_name = get_user_contributed_name()
    # TODO: Check if person is already in local db
    # TODO: Encode the image and compare it to those in the local db
    # move file to a folder labeled with the firstname_lastname
    # call for rekognition or my desktop to process facial mapping
    # check if this person is already in MY db and get comparison confidence
        # if high confidence or doesn't exist -> add to db with confidence=1
        # if low confidence -> Refuse, state confidence, continue with IR search


def manual_labeling(file_name):
    """
    Method to ask the user if they would like to contribute an unmatched person to the
    local facial recognition database.
    :param file_name: Name of the file stored in S3 to save to the local facial recognition database.
    :return: If the user wants to contribute: ((First Name, Last Name), Face matching confidence)
             Else: False
    :rtype: Tuple(Tuple(str, str), float) or bool
    """
    print(f"AWS Rekognize was unable to recognize the face provided in \"{file_name}\"")
    while True:
        contribute = (
            input("Would you like to contribute to this IR system by providing this person's name? (y/n): ").lower())
        if contribute == 'y' or contribute == 'yes':
            tup = user_contribution(file_name)  # tup = ((First name, Last name), confidence)
            return tup
        elif contribute == 'n' or contribute == 'no':
            # End program
            return False
        else:
            print("Unable to interpret your response...")
            continue
