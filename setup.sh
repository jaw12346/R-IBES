#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if the script is run with sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run this script as root or with sudo${NC}"
  exit 1
fi

# Read flags
while getopts "hd" flag; do
 case $flag in
   h) # Handle the -h flag
   # Display script help information
    echo "Usage: setup.sh [-h] [-d]"
    echo "-h: Display help information"
    echo "-d: Enable download mode (downloads the ontologies file from DBPedia for database creation)."
    exit 0
   ;;
   d) # Handle the -d flag
   # Enable developer mode
   download_mode=true
   echo "Download mode enabled!"
   ;;
   # Process the specified file
   \?)
   # Handle invalid options
    echo -e "${RED}Invalid option: -$OPTARG${NC}" >&2
   ;;
 esac
done

# Update the package list and upgrade the installed packages
#apt-get update && apt-get upgrade -y

# Install the system dependencies from requirements.system
echo -e "${YELLOW}Installing the system dependencies from requirements.system${NC}"
cat requirements.system | xargs apt install -y
echo -e "${GREEN}Finished installing system dependencies${NC}"

pip3 install virtualenv

VENV_DIR="venv"
ACTIVATE_FILE="./venv/bin/activate"
if [ ! -d "$VENV_DIR" ]; then
  # Create a virtualenv with the given name and Python 3
  echo -e "${YELLOW}Creating a virtual environment named 'venv' with Python 3${NC}"
  python3 -m venv venv
else
  echo -e "${GREEN}Virtual environment 'venv' already exists!${NC}"
fi

# Activate the virtualenv
echo -e "${YELLOW}Activating the virtualenv${NC}"
source "$ACTIVATE_FILE"

# Install the Python dependencies from requirements.txt
echo -e "${YELLOW}Installing the Python dependencies from requirements.txt${NC}"
pip3 install wheel
pip3 install -r requirements.txt

# Download the spacy model
echo -e "${YELLOW}Downloading the spacy model 'en_core_web_md'${NC}"
python3 -m spacy download en_core_web_md

if [ "$download_mode" = true ] ; then
  # Download the ontologies file from DBPedia
  echo -e "${YELLOW}Downloading the ontologies file from DBPedia${NC}"
  wget -O ontologies.ttl.bz2 https://downloads.dbpedia.org/current/core/mappingbased_objects_en.ttl.bz2

  # Extract the ontologies file
  echo -e "${YELLOW}Extracting the ontologies file${NC}"
  lbzip2 -d ontologies.ttl.bz2
fi

# Print a success message
echo -e "${GREEN}Done!${NC}"
echo -e "${GREEN}Activate the virtual environment by running 'source venv/bin/activate' and run the app with 'python3 main.py'${NC}"
