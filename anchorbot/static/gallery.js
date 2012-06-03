var offset = 0;
var key_offset = {};

function new_article(art) {
  // Build up keyword button list
  buttons = $("<div/>", {
    'class': 'small',
  }).append(
    $("<span/>", {
      style: "font-size:50%",
      html: "Release: "+Humanize.naturalDay(parseInt(art.datestr))+"<br>Why do you want to read this?"
    })
  );
  $.each(art.keywords, function(l, key) {
      $("<a/>", {
        'class': "button",
        html: key.word,
        style: "margin-left:5pt;"
      }).click(function() {
          $.getJSON('/_like/id/'+key.ID, function() {
              window.location = "/key/"+key.word;
          });
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
  $.getJSON('/json/top/art/'+kid+'/'+(key_offset[kid]+3)+"/3", function(data) {
    $.each(data.articles, function(i, art) {
      frame = gallery.children(".issue2:eq("+i+")");
      $.getJSON('/skip/'+frame.attr("id"), function(d) {});
      frame.after(
          new_article(art).fadeIn()
        ).fadeOut(
          'fast',
          function() {
            $(this).remove();
          });
      key_offset[kid]++;
    });
    /* skip the rest, too */
    children = gallery.children(".issue2");
    if(children.length > data.articles.length){
      children.slice(data.articles.length).each(function(i) {
        $.getJSON('/skip/'+$(this).attr("id"));
        /* fade gallery out if empty */
        if(data.articles.length <= 0) {
          $("#container .gallery#"+kid).animate(
            {
              width: 0,
              opacity: 0.0
            },
            'fast',
            function() {
              $(this).remove();
            });
          load_gallery(offset);
          offset++;
        } else {
          $(this).animate(
            {
              height: 0,
              opacity: 0.0
            },
            'fast',
            function() {
              $(this).remove();
            })
        }
      });
    }
  });
}

hate_and_hide = function(kid) {
  $.getJSON('/_hate/id/'+kid, function(data) {
      $("#container .gallery#"+data.kid).animate(
        {
          width: 0,
          opacity: 0.0
        },
        'fast',
        function() {
          $(this).remove();
        });
      load_gallery(offset);
      offset++;
  });
}

function load_gallery(offset) {
  $.getJSON('/json/top/key/'+offset+"/1", function(data) {
    if(data.keywords.length > 0) {
      /* add new container for each key */
      $.each(data.keywords, function(i, kw) {
        key_offset[kw.ID] = 0;
        $.getJSON('/json/top/art/'+kw.ID+'/'+key_offset[kw.ID]+"/3", function(data) {
          gallery = $('<div/>', {
              'class': "gallery",
              title: kw.word,
              id: kw.ID
              }
          ).append(
            $("<a/>", {
                'class': "hate",
                text: "X ",
                title: "Hate '"+kw.word+"'",
                style: "cursor: pointer;"
            }).click(function() {hate_and_hide(kw.ID);})
          ).append(
            $("<a/>", {
                'class': "title",
                id: kw.ID,
                html: kw.word,
                title: "Show more on '"+kw.word+"'",
                style: "cursor: e-resize;"
            }).click(function() {load_more(kw.ID);})
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
  load_and_inc_offset(1);
  load_and_inc_offset(1);
  load_and_inc_offset(1);
  load_and_inc_offset(1);
  load_and_inc_offset(1);

  /*$(window).scroll(function() {
    if(1.2*$(window).scrollLeft() >= $(document).width() - $(window).width()) {
      load_gallery(offset);
      offset++;
    }
  });*/
});
