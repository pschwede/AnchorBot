AnchorBot
=========

The idea is simple. Usually when reading the news, it takes most of the time to
fish for interesting news in the ocean of news. Now, AnchorBot tries to
automate it by fishing out news that share a headline word you were interested
in before. You start with a bunch of totally random news articles displayed
with an headline and a picture. If you want to read an article, you have to
click a word in the headline that is most interesting to you. For example:

In "Google buildt UFO" you can decide whether you are more interested in UFO or
in Google. Each word got it's own link.

By repeatingly making rather quick choices like this. Anchorbot will show
articles of your choice first. If you clicked Google, it'll be news about
google. If you clicked UFO, it'll be news about UFO not Google.
Articles are weighted by the weight of the words they have in the headline.

Anchorbot presents the news page-wise. That way you can get a quick overview.
Reloading the page, you will get a next interest-adopted collection.
Note that, to harness the daily flush of news, each article is displayed only once!

*TLDR*: It's a simple learning news feed aggregator and surprisingly works well.


Features
--------
* Supported feeds: RSS, ATOM (you can also observe HTML with additional software)
* Completely runs on your machine. You store your data on your own. No obscure
  cloud. New articles and non-text media still require internet connection, of
  course.


Start crawling:

```bash
python bot.py
```

Start interface:

```bash
python web.py
firefox localhost:8000
```

Thanks to redis, you can run both in the same time. But remember, that you get
the best effect after having collected ALL TEH NEWS!


What I need help with
---------------------
* Get a nice adaptive CSS for the news feed.
* Let the user adjust the amount of articles per page.

* For more information on planned features, please read the [Wiki](http://github.com/spazzpp2/AnchorBot/wiki).
* For feature requests and other discussions, please visit the [Subreddit](http://www.reddit.com/r/anchorbot).


