#!/usr/bin/python
import os
from setuptools import setup

def read(fname):
  return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
  name = "AnchorBot",
  version = "1.0",
  author = "spazzpp2",
  author_email = "",
  description = ("Feed reader + Microblogging assistant"),

  license = "MIT",
  keywords = "rss feed reader twitter identica microblogging",
  install_requires = [
    'setuptools',
    "pygtk",
    "pywebkitgtk", 
    "feedparser", 
    "lxml", 
    "hyphenator", 
    "tweepy", 
    "sqlalchemy", 
    "sqlite3",
    ],
  url = "http://github.com/spazzpp2/AnchorBot",
  packages = ["anchorbot", "tests"],
  long_description = read("README.md"),
  classifiers = [
    "Development Status :: 3 - Beta",
    "Topic :: Utilities",
    "License :: OSI Approved :: MIT License",
    ],
)
