AnchorBot
=========

*Version 1.0 beta*

*© spazzpp2 – Licensed under MIT License*

It's a news aggregator with the attempt of making you read the most important news first.

Features
--------
* Get pictures, videos, audio, etc. out of the feeds or the page they're linking to
* Microblogging support
* Analyze feed entries for repeatations in microblogs or other feeds to merge and sort
* Focus on readability

Installation
------------
Python >= 2.7 needed!

*Ubuntu:*

    sudo setup.ubuntu.sh
    ./anchorbot.linux

*all other:*

    setup.py install

*Windows:*

Tell me ;)

How to Use
----------
* Click the Add-Button to append a rss-url to your list
* Click a feed to read.
  * Click "Source" to call your web browser to show the complete webpage
  * Click "Share" to dent the link
* Click a feed again to refresh it.
* Click the Reload-Button to refresh all feeds

*⚠ Running it the first time may take some minutes even with a fast Internet 
connection!*

The Idea
--------
I had the feeling that I should discribe this more and why I started this:

I suppose, you have this situation almost everyday, and I made some review
about this:

Basically I started my browser to see what's going on. I usually iterated
through a static list of bookmarks: news pages, blogs, forums, reddit, twitter
and even some static html files and checked them for exciting stuff I should
read, listen to, watch or bookmark for tomorrow. You may see, that this 
takes a lot of time and although entertaining here and there, I felt like 
this was not ompletely worth the efford. Doing this every day just to satisfy 
my little addiction to good news wasn't making it any better.

Usually I've been flooded by tweets & articles that are
* not your interest (Some software has been attacked, you don't use, etc.)
* redundant (Many news sites tell the same story a little different so in 
the end you are confronted with them more than nessesary. Even if you're not 
interested in them, you have to actively decide to skip them)
* unreadable (Because of ads and bad design)
* shortlinked (So you think it's some interesting link you haven't clicked yet)
* invisible by differences in design (Switching from one news site to another takes
some efford of orientation)
* many (About 10 news pages with about 5 probably interesing links each = 
50 new tabs!)
* textwalls (You won't read them, because you hope there's somewhere 
another version with more illustrations)
* finally really interesting (So that you would like to know more about it 
past or future)

So I thought about the problem, with which I heard I am not alone:

On the one hand I could have decided to ignore all the news storm 

And I checked existing methods to handle this flood:
* RSS feed readers automatically check pages for news and display them in an
equal way (Browser extensions like Readability unify, too, but fail some times)
* Reddit and other bookmark communities vote up interesting stuff (Users click 
the up-arrow) so, ideally, there's a Highscore of must-see content. Also, Twitter
 friends post stuff they recommend to look at (it could also be regarded as up-vote)
* Browser extensions like read-it-later, update-scanner help with timing and 
observation
* Automated content curators like Paper.li make layouted summaries of tweeted
content but don't really fit my needs.
* Feed.ly is a proprietary server based interface for Google Reader with some 
internal, intransparent upvote-mechanisms. But you need to use your Google 
Account Cookie in order to use it.

Well they all are nice ideas, but they would all be of better use, if working all 
together. Additionally I thought about the majority of personal computers that run
and idle while showing some text in a browser.

So I came to the idea to write a script that does the main things I needed:
Pull rss-feeds and other news streams and find out what might the reader
interest the most. The importance of news could be detected by:
* the number sources that posted about the same topic/keyword (including friends)
* the number of readings of articles with the same keyword

Also, for more comfort, my reader should:
* merge articles that share the same story and present them to the user on demand
* gather images and more text about the story in the case it's not illustrative, 
intuitive enough or needs to be "clicked for more"
* fold together similar topics, to also show the lesser scoring articles
* provide an ability to upvote articles on social communities
* (in future) reduce down-traffic by sharing the curation work with friends
* (in future) build a p2p news network

So, this is what I came up with so far.

Related Projects
----------------
* [Flipboard](http://flipboard.com/)
* [Hotot](https://code.google.com/p/hotot)
* [Google Reader](http://reader.google.com/)
* [Scrolldit](http://scrolldit.com/)

This project was once known as "Lyrebird" and is - as before - still a tribute to the 
[bird that retweets](http://youtu.be/7XiQDgNUEMw) the terrifying chainsaws that sew 
down it's rain forest.
