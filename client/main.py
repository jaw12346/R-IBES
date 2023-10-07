import user_contribution
import aws_rekognition
import s3_operations
from pyfiglet import Figlet


def welcome_interface():
    f = Figlet(font='bulbhead')
    print(f.renderText('R-IBES'))  # Reverse-Image Biographical Entity Search -- R-IBES


def main():
    # welcome_interface()
    file_name = s3_operations.upload_process()
    # file_name = "IMG_1935.jpg"
    label = aws_rekognition.detect_labels(file_name)
    if not label:
        label = user_contribution.manual_labeling(file_name)
    s3_operations.cleanup(file_name)


if __name__ == '__main__':
    # main()
    s3_operations.download_from_aws('George_W_Bush_0528.jpg')

