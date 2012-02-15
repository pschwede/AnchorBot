function getURL() {
  var pos = window.location.href.indexOf(window.location.host);
  return window.location.href.substring(0, pos+window.location.host.length);
}

var otheroff = 0;
var offset = 0;
var offx = 0;
var offy = 0;

$('document').ready(function() {
  $('#feeds').focusin(function() {
    $("#popup_content").load(
      getURL()+"/_feeds", 
      function() {
        $("#popup").slideDown("medium", function() {});
      }
      );
  }).focusout(function() {
    $("#popup").slideUp('fast');
  });

  $('#keywords').focusin(function() {
    $("#popup_content").load(
      getURL()+"/_keywords", 
      function() {
        $("#popup").slideDown("medium", function() {});
      }
      );
  }).focusout(function() {
    $("#popup").slideUp('fast');
  });

  $('.content').load(
      getURL()+"/gallery/key/offset/0,0",
      function() {
      }
      ).fadeIn('slow');

    if($(window).scrollTop() >= $(document).height() - $(window).height() - 40) {
      offset+=1;
      $('#container').append('<div class="content"></div>');
      $('.content:last').load(
        getURL()+"/gallery/key/offset/"+offset+",0"
      );
    }

  $(window).scroll(function() {
    if($(window).scrollTop() >= $(document).height() - $(window).height() - 40) {
      offset+=1;
      $('#container').append('<div class="content"></div>');
      $('.content:last').load(
        getURL()+"/gallery/key/offset/"+offset+",0"
      );
    }
  });
});
