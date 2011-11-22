#!/bin/bash

# Please read install scripts before running them!

# this will install all needed python modules and libraries to build lxml
apt-get install python-feedparser python-sqlite python-setuptools libxml2-dev libxslt1-dev python2.7-dev &&

# this will download newest packages and install them
easy_install hyphenator tweepy beautifulsoup lxml sqlalchemy
