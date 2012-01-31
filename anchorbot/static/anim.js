function getURL() {
  var pos = window.location.href.indexOf(window.location.host);
  return window.location.href.substring(0, pos+window.location.host.length);
}

var offset = 0;

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

  $('#galery').load(
      getURL()+"/offset/0",
      function() {
        $("#content").fadeIn("slow");
      }
      );

  $(window).scroll(function() {
    if($(window).scrollTop() >= $(document).height() - $(window).height() - 40) {
      offset+=1;
      $('#galery').append('<div id="galery'+offset+'"></div>');
      $('#galery'+offset).load(
        getURL()+"/offset/"+offset
      );
    }
  })
});
