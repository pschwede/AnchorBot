function getURL() {
  var pos = window.location.href.indexOf(window.location.host);
  return window.location.href.substring(0, pos+window.location.host.length);
}

var otheroff = 0;
var offset = 0;
var offx = 0;
var offy = 0;
var known_keys = [];

function load_gallery(offset) {
  $.getJSON('/gallery/key/top/'+offset, function(data) {
    /* add new container for each key */
    $.each(data.keywords, function(i, kw) {
      $('<div/>', {
        'class': "gallery",
        id: kw.word,
        html: '<a href="/key/'+kw.word+'"><h1>'+kw.word+'</h1></a>'
      }).appendTo("#container");
      $.getJSON('/gallery/art/top/'+kw.ID+'/'+offset, function(data) {
        $.each(data.articles, function(j, art) {
          buttons = [];
          $.each(art.keywords, function(l, key) {
            buttons.push('<a class="button" href="/key/'+key.word+'">'+key.word+'</a>');
          });
          $("<div/>", {
            'class': 'issue2',
            id: art.ID,
            style: "background-image: url("+art.image.filename+");",
            html: '<h2 class="issue_head">'+art.title+'</h2>'
          }).append(
            '<div class="small"><span style="font-size:50%;">Why do you want to read this?</span><div class="tags">'
            +buttons.join(" ")
            +'</div></div>'
            ).appendTo("#container #"+kw.word);
          $("#container #"+kw.word).fadeIn();
        });
      });
    });
  });
}

load_and_inc_offset = function(delay) {
  load_gallery(offset);
  offset++;
  if($(document).height()-4 < $(window).height()) {
    setTimeout("load_and_inc_offset(delay)", delay);
  }
}

$('document').ready(function() {
  $('#feeds').click(function() {
    $("#popup_content").load(
      getURL()+"/_feeds", 
      function() {
        $("#popup").slideDown("medium", function() {});
      }
      );
  }).click(function() {
    $("#popup").slideUp('fast');
  });

  $('#keywords').click(function() {
    $("#popup_content").load(
      getURL()+"/_keywords", 
      function() {
        $("#popup").slideDown("medium", function() {});
      }
      );
  }).click(function() {
    $("#popup").slideUp('fast');
  });

  load_and_inc_offset(5000);

  $(window).scroll(function() {
    if(1.2*$(window).scrollTop() >= $(document).height() - $(window).height()) {
      load_gallery(offset);
      offset++;
    }
  });
});
