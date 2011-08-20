# -*- encoding: utf-8 -*-
from time import localtime, strftime

def keyword(kw):
    return "<a class=\"button\" href=\"about:more?key=%s\">%s</a>" % (kw.ID, kw.word)

def about_button(service, link, text=None):
    return {
            "source": '<a class="about_source button" href="%s">Source</a>' % link,
            "share": '<a class="about_share button" href="about:share?url=%s&text=%s">Share</a>' % (link, text,),
            }[service]

def art_gallery(article):
    """The feed-entry inside the browser."""
    title = article.title.encode("utf-8")
    image = u""
    buttons = u""
    if article.image:
        image = '%s' % article.image.filename
    if article.link:
        buttons = about_button("source",article.link) + about_button("share",article.link,article.title)
    return u"""\
            <div class="issue2" style="background-image:url(%s);">
                <h2 class="issue_head" title="%s">%s</h2>
                <div class="small">
                    <div>%s</div><div class="tags">%s</div>
                    <div>%s</div>
                </div>
            </div>
            """ % (
                    image,
                    title, title,
                    strftime(u"%X %x", localtime(article.date)),
                    u"".join([keyword(kw) for kw in sorted(article.keywords, key=lambda x: x.clickcount)]),
                    buttons,
                    )

def art_read(article):
    title = article.title.encode("utf-8")
    image = ""
    buttons = ""
    if article.image:
        image = """<div class="image"><img src="%s" alt=""/></div>""" % article.image.filename
    if article.link:
        buttons = about_button("source",article.link) + about_button("share",article.link,article.title)
    """The feed-entry inside the browser."""
    return u"""\
            <div class="issue1">
                <h2 class="issue_head" title="%s">%s</h2>
                %s
                <div class="issue_content">%s</div>
                <div class="small">
                    <span class="time">%s</span>
                    <span class="keywords">%s</span>
                    %s
                </div>
            </div>
    """ % (
            title, title,
            image,
            article.content,
            strftime("%X %x", localtime(article.date)),
            u"".join([keyword(kw) for kw in sorted(article.keywords, key=lambda x: x.clickcount)]),
            buttons,
            )

def article(article, mode=0):
    if mode is 1:
        return art_gallery(article)
    else:
        return art_read(article)
