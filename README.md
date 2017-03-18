# AnchorBot

## TL;DR

A (prototype of a) simple learning news feed aggregator working surprisingly well.

**Note:** I plan to redo this piece of software very soon.


## Introduction

The idea is simple. Usually when reading the news, it takes most of the time to
search for news you are interested in. AnchorBot tries to automate this by
looking through your RSS/Atom feeds: Which articles share a keyword you
had been interested in before?

Anchorbot weights articles by the count of how many times your clicked a word
in the headline. It then presents the news in a grid page by page. That way you
can get a quick overview.

Currently, each article is displayed only once. So read carefully!


## Features

* support RSS and ATOM feeds
* scrape full text and embedded media from articles (as do [Instapaper](https://instapaper.com), [Readability](https://readability.com))
* highlight the keyword, the first and last sentence in paragraphs (anatomy of an article)
* server runs on local machine.

## Missing

* user friendly UI for managing feeds and keywords and stopping the program
* display article author
* Android app / reactive web interface

## Setup

### Requirements

* a running [Redis](https://redis.io) service


## Usage

### Adding

### Start reading

```bash
./start.sh & firefox 0.0.0.0:8000
```

### Stop

Currently not implemented! Try killing all the anchorbot jobs:

```bash
pkill -f 'anchorobt.*py'
```

## More info

* For more information on planned features, please read the [Issues](http://github.com/pschwede/AnchorBot/issues).
