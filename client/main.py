import aws_rekognition
import s3_operations
from pyfiglet import Figlet

from server import local_facial_recognition as lfr
import user_contribution


def welcome_interface():
    f = Figlet(font='bulbhead')
    print(f.renderText('R-IBES'))  # Reverse-Image Biographical Entity Search -- R-IBES


def local_search(search_file_location):
    test_encoding = lfr.generate_face_encoding(search_file_location, debug=False)
    most_likely_person = lfr.identify_person_from_encoding(test_encoding, debug=False)
    return most_likely_person


def aws_search(search_file_location):
    """
    Search for a person using AWS Rekognition.

    :param search_file_location: Local location of the file to search for using AWS
    :type search_file_location: str
    :return: AWS-detected person name or False if no person was detected
    :rtype: awsPersonTup or bool
    """
    # s3_file_name = s3_operations.upload_process()
    file_name = search_file_location.split('\\')[-1]
    uploaded = s3_operations.upload_to_aws(search_file_location, file_name)
    if uploaded:
        detected_celebrity = aws_rekognition.detect_labels(file_name)
        if detected_celebrity:
            s3_operations.cleanup(file_name)
            return detected_celebrity
        print("No celebrity detected by AWS.")
        s3_operations.cleanup(file_name)
        return False
    print("Unable to upload file to AWS S3.")
    return False


def main():
    # Attempt to detect person using local db
    search_file_location = './test_images/Hazel_Dellario/Hazel_Dellario_0001.jpg'
    # search_file_location = s3_operations.get_file_from_user()
    most_likely_person = local_search(search_file_location)
    print(f'Most likely person: {most_likely_person}')

    # If local db fails, attempt to detect person using AWS Rekognition
    if most_likely_person == 'UNKNOWN':
        aws_detected = aws_search(search_file_location)
        if not aws_detected:
            contribution = user_contribution.manual_labeling(search_file_location)
            if not contribution:
                # User did not want to contribute to the DB
                # End the program
                return


        print(f'Most likely person: {aws_detected}')
        # TODO: Implement manual_labeling and user_contribution in user_contribution.py
        # person_name = user_contribution.manual_labeling(s3_file_name)


if __name__ == '__main__':
    main()
    # s3_operations.download_from_aws('George_W_Bush_0528.jpg')
