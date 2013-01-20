AnchorBot
=========

It's a news feed reader with the attempt of making you read the most important
news first.


Features
--------
* gets videos and pictures out of the RSS feeds and the page they're linking to
* analyzes feed entries for repeatations in microblogs or other feeds to merge and sort
* focus on readability
* locally hosted webinterface to run inside your browser

For more information, please read the [Wiki](http://github.com/spazzpp2/AnchorBot/wiki).


Installation
------------
Needs Python at least as new as 2.6.

*Ubuntu:*

    sudo setup.ubuntu.sh

*all other:*

    setup.py install


Usage
-----
To add rss/atom feeds (not implemented in web interface yet), append a line
with your feed-url to `~/.ancorbot/abos`.

    echo "yourfeedurl" >> ~/.anchorbot/abos

Or call `bot.sh --add yourfeedurl`.

Call `bot.sh` to run the downloading and analyzing bot. Be sure to have internet connection.

Execute `web.sh` to run the server and open your webbrowser with it's url.


Related Projects
----------------
* [rawdog](http://offog.org/code/rawdog.html)
* [Prismatic](http://www.getprismatic.com/)
* [Flipboard](http://flipboard.com/)
* [Hotot](https://code.google.com/p/hotot)
* [Google Reader](http://reader.google.com/)
* [Scrolldit](http://scrolldit.com/)
* [TweetMag](http://www.tweetmagapp.com/)
* [Summify](http://summify.com/)
* [News.me](http://news.me/)


*Version 1.0 beta*

*© spazzpp2 – Licensed under MIT License*

This project was once known as "Lyrebird" and is - as before - still a tribute
to the [bird that retweets](http://youtu.be/7XiQDgNUEMw) the terrifying
chainsaws that sew down it's rain forest.
