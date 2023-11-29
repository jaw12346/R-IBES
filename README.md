# R-IBES: Reverse-Image Biological Entity Search

## Project Description

_R-IBES is a reverse-image search engine utilizing the power of local and cloud-based facial recognition to answer
biographical questions about public figures. This implementation uses a local Postgres database that’s pre-populated
with over 13k images of celebrities. When an unknown face is provided, R-IBES queries AWS Rekognize for the person’s
name and/or asks the end-user to contribute, thus adding that person to the dataset with the goal of limiting cloud
usage as more people are searched._

Project documentation can be accessed by opening `/docs/index.html` in a web browser.

## Installation instructions (with a DB file)
__Note: R-IBES has only been tested on Ubuntu 22.04.3 LTS via WSL2 using Python 3.10.12__

1) Clone the repo into a local directory of your choice (if it hasn't already been provided to you)
    ```shell
    git clone https://github.com/jaw12346/R-IBES.git
    ```
   
2) Run the following command in your Ubuntu instance to install prerequisites:
    ```shell
    sudo apt-get install python3 python3-pip python3-venv graphviz graphviz-dev imagemagick
    ```

3) Navigate into the project directory and install the required pip packages
    ```shell
    pip3 install -r requirements.txt
    ```

4) If you have a database file, place it into the project directory.

5) (Optional) Open `.env` and change the following variables to match your environment:
    ```shell
    S3_BUCKET=your_s3_bucket_name
    S3_ACCESS_KEY=your_aws_s3_access_key
    S3_SECRET_KEY=your_aws_s3_secret_key
    ```

6) Run the following command to start R-IBES:
    ```shell
    python3 main.py [--offline]
    ```
   __Note:__ If you do not have a S3 bucket or keys, please add `--offline` to the startup command.
