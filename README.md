# AnchorBot

A (prototype of a) simple learning news feed aggregator that works surprisingly well.

**Note:** I plan to redo this piece of software very soon.


## Why?

While journalism is regarded as the fourth column the western society is
standing on, the introduction of web 2.0 caused a disruption in the
journalistic ecosystem.  News are all over the place.  Blogs, newspapers and
broadcasting services mangle together in one web of relevant and irrelevant
articles with a wide range of quality.

Reading news can be very frustrating today:

* Centristic shareholders influence framing and relevance decisions
* Social networks resonate echo chambers
* Style variety, ads and click-bait poison your attention

Anchorbot delivers.  It additively merges several newsrooms into an automated
personal one.  It presents the news in a way that is easy to the senses and
helps you to concentrate on the important things, not the loudest.  You decide
upon the relevance of headlines.

## Features

* Subscribe to RSS and ATOM feeds
* Scrape full text and embedded media from articles (similar to [Instapaper](https://instapaper.com) and [Readability](https://readability.com))
* Highlight selected keyword, the first and last sentence in [paragraphs](https://de.slideshare.net/amandacpoiesis/anatomy-of-a-paragraph)
* Bot and interface run on local machine. No trust on cloud services required.

## Missing features

* User friendly UI for managing feeds and keywords and stopping the program
* Display article author
* Android app
* reactive web interface

## Setup

### Requirements

* an installed Python 2
* a running [Redis](https://redis.io) service
* probably Linux (nothing else tested)

### Install

Run the following as root:

```bash
pip2 install justext Pillow redis_collections flask flask-markdown
git clone https://github.com/pschwede/AnchorBot.git
cd AnchorBot
```

This command assumes that `pip2` is pip for Python 2.
From here continue with [Usage](#usage).

## Usage

### 1. Run the bot

```bash
./bot.py
```

### 2. Add subscriptions

Add urls to `~/.config/anchorbot/config`.

### 3. Start reading

```bash
./start.sh & firefox 0.0.0.0:8000
```

### 4. Stop

Currently not implemented! Try to kill all the anchorbot jobs:

```bash
pkill -f bot.py
pkill -f web.py
pkill -f start.sh
```
