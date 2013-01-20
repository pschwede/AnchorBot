AnchorBot
=========

It's a learning news feed aggregator.


Features
--------
* Supported feeds: RSS, ATOM (you can also observe HTML with additional software)
* Completely runs on your machine. You store your data on your own. No obscure
  cloud. New articles and non-text media still require internet connection, of
  course.
* Adds missing media in news feeds to the article (like text, video or bigger images)
* Embedded Media: Images, Vimeo, YouTube

For more information on planned features, please read the [Wiki](http://github.com/spazzpp2/AnchorBot/wiki).


Installation
------------
Ubuntu:

    sudo setup.ubuntu.sh

Other:

    setup.py install

Please report missing libraries to me.


Usage
-----
Add new feed urls:

    echo "yourfeedurl" >> ~/.anchorbot/abos

Alternatively:

    bot.sh --add yourfeedurl

Start crawling:

    bot.sh

Start interface:

    web.sh

Try not to run both, `bot.sh` and `web.sh`! (I will fix concurrency later.)

Please report bugs at [Github](https://github.com/spazzpp2/AnchorBot/issues)!


Related Projects
----------------
* [rawdog](http://offog.org/code/rawdog.html) – Frequently download and render news feeds to HTML (OS)
* [Prismatic](http://www.getprismatic.com/) – Filtering, personal social news aggregator
* [Flipboard](http://flipboard.com/) – Magazine-like news aggregator and curator
* [Google Reader](http://reader.google.com/) – Google's news aggregator
* [Scrolldit](http://scrolldit.com/) – Pinwall interface for reddit (OS)
* [newssitter](http://www.newssitter.com) – Display news feeds in Firefox' sidebar (OS)

(OS = Open Source)


*© spazzpp2 – Licensed under MIT License*

This project was once known as "Lyrebird" and is - as before - still a tribute
to the [bird that retweets](http://youtu.be/7XiQDgNUEMw) the terrifying
chainsaws that sew down it's rain forest.
