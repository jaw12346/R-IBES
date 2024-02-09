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

# Update the package list and upgrade the installed packages
#apt-get update && apt-get upgrade -y

# Install the system dependencies from requirements.system
echo -e "${YELLOW}Installing the system dependencies from requirements.system${NC}"
cat requirements.system | xargs apt install -y
echo -e "${GREEN}Finished installing system dependencies${NC}"

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

# Print a success message
echo -e "${GREEN}Done!${NC}"
echo -e "${GREEN}Activate the virtual environment by running 'source venv/bin/activate' and run the app with 'python3 main.py'${NC}"
