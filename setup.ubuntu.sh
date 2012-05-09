#!/bin/bash

# Please read install scripts before running them!

# this will install all needed python modules and libraries to build lxml
apt-get install libxml2-dev libxslt1-dev python2.7-dev &&

# this will download newest packages and install them
pip install feedparser sqlite setuptools tweepy beautifulsoup lxml sqlalchemy
