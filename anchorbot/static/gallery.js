var offset = 0;
var key_offset = {};
var vert_num = 3;
var hori_num = 5;  // unused

function new_article(art) {
  // Build up keyword button list
  buttons = $("<div/>", {
    'class': 'small',
  }).append(
    $("<span/>", {
      style: "font-size:50%",
      html: "Release: "+Humanize.naturalDay(parseInt(art.datestr))
    })
  ).append(
    $("<div/>", {
      style: "font-size:50%; width: 100%;",
      html: "Why do you want to read this?"
    })
  );
  $.each(art.keywords, function(l, key) {
      $("<a/>", {
        'class': "button",
        html: key.word,
        title: "/read/"+art.ID,
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
  gallery = $("#content .gallery#"+kid);
  // hate current articles
  var hated_ids = new Array();
  gallery.children(".issue2").each(function(i, issue) {
    hated_ids[i] = issue.id;
  });
  $.getJSON('/json/top/art/'+kid+'/'+(key_offset[kid]+3)+"/"+vert_num, function(data) {
    if(data.articles.length <= 0) {
      // hide the whole gallery
      gallery.animate({width: 0, opacity: 0.0},
        'fast', function() {$(this).remove();});
      for(int i=$("#content .gallery").length; i<hori_num; i++) {
        load_gallery(offset);
        offset++;
      }
    } else {
      // insert the new
      $.each(data.articles, function(i, new_one) {
        $("#content .gallery#"+kid).children(".issue2:eq("+i+")").fadeOut(
          "fast", function() {
            $(this).remove();
            new_article(new_one).appendTo("#content .gallery#"+kid).fadeIn();
          });
      });
      key_offset[kid]++;
    }
  });
  // really hating
  $.each(hated_ids, function(i, id) {
    $.getJSON('/skip/'+id, function() {});
  });
}

hate_keyword = function(kid) {
  $.getJSON('/_hate/id/'+kid, function(data) {
      $("#content .gallery#"+data.kid).animate(
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
      /* add new div for each key */
      $.each(data.keywords, function(i, kw) {
        key_offset[kw.ID] = 0;
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
          }).click(function() {hate_keyword(kw.ID);})
        ).append(
          $("<a/>", {
              'class': "title",
              id: kw.ID,
              html: kw.word,
              title: "Show more on '"+kw.word+"'",
              style: "cursor: e-resize;"
          }).click(function() {load_more(kw.ID);})
        ).appendTo("#container #content");
        $.getJSON('/json/top/art/'+kw.ID+"/"+key_offset[kw.ID]+"/"+vert_num, function(data2) {
          $.each(data2.articles, function(j, art) {
            $(".gallery#"+kw.ID).append(new_article(art)).fadeIn("slow");
          });
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
});
