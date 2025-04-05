#!/bin/bash
# install.sh

# Install Python and dependencies
echo "Installing Python and dependencies..."
apt-get update  # For Debian/Ubuntu-based systems
apt-get install -y python3 python3-pip
pip3 install -r requirements.txt

# Run the app with Gunicorn
echo "Starting Bookmarks app..."
python3 -m gunicorn --bind 0.0.0.0:5000 run:app