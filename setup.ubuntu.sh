#!/bin/bash
echo "I recommend to read install scripts before running them!"

# this will make sure, the recommended python version is available
apt-get install python2.7-dev &&

# this will download newest python modules and installs them
pip install feedparser sqlite setuptools tweepy beautifulsoup lxml sqlalchemy
