var offset = 0;
var key_offset = {};

function new_article(art) {
  // Build up keyword button list
  buttons = $("<div/>", {
    'class': 'small',
  }).append(
    $("<span/>", {
      style: "font-size:50%",
      html: "Why do you want to read this?"
    })
  );
  $.each(art.keywords, function(l, key) {
      $("<a/>", {
        'class': "button",
        href: "/key/"+key.word,
        html: key.word,
        style: "margin-left:5pt;"
      }).appendTo(buttons);
  });
  // append article to gallery of keyword
  return $("<div/>", {
    'class': 'issue2',
    id: art.ID,
    style: "background-image: url("+art.image.filename+");"
  }).append(
    $("<h2/>", {
      'class': 'issue_head',
      html: art.title
    })
  ).append(buttons);
}

function load_more(kid) {
  gallery = $("#container .gallery#"+kid);
  /* replace the old */
  $.getJSON('/json/top/art/'+kid+'/'+(key_offset[kid]+5), function(data) {
    $.each(data.articles, function(i, art) {
      frame = gallery.children(".issue2:eq("+i+")");
      $.getJSON('/skip/'+frame.attr("id"), function(d) {});
      frame.after(new_article(art).fadeIn()).fadeOut().remove();
      key_offset[kid]++;
    });
    /* skip the rest, too */
    children = gallery.children(".issue2");
    if(children.length > data.articles.length){
      children.slice(data.articles.length).each(function(i) {
        $.getJSON('/skip/'+$(this).attr("id"), function(d) {
        });
        $(this).fadeOut().remove();
        /* fade gallery out if empty */
        if($("#container .gallery#"+kid+" .issue2").length <= 0)
          gallery.fadeOut().remove();
      });
    }
  });
}

function load_gallery(offset) {
  $.getJSON('/json/top/key/'+offset, function(data) {
    if(data.keywords.length > 0) {
      /* add new container for each key */
      $.each(data.keywords, function(i, kw) {
        key_offset[kw.ID] = 0;
        $.getJSON('/json/top/art/'+kw.ID+'/'+key_offset[kw.ID], function(data) {
          gallery = $('<div/>', {
            'class': "gallery",
            id: kw.ID
          }).append(
            $("<a/>", {
              id: kw.ID
              //href: "/key/"+kw.word
            }).append(
              $("<h1/>", {
                html: kw.word,
                style: "cursor: e-resize;"
              })
            ).click(function() {load_more(kw.ID);})
          ).appendTo("#container");
          $.each(data.articles, function(j, art) {
            new_article(art).appendTo(gallery);
          });
          $(gallery).fadeIn('slow');
        });
      });
    }
  });
}

load_and_inc_offset = function(n) {
  if(n <= 0) return;
  load_gallery(offset);
  offset++;
  load_and_inc_offset(n-1);
}

fill_up = function(kid) {
  if($(window).scrollTop() >= $(document).height() - $(window).height()) {
    load_and_inc_offset(1);
  }
  setTimeout("fill_up()", 1000);
}

$('document').ready(function() {setup();
  fill_up()

  $(window).scroll(function() {
    if(1.2*$(window).scrollTop() >= $(document).height() - $(window).height()) {
      load_gallery(offset);
      offset++;
    }
  });
});
