function getURL() {
  var pos = window.location.href.indexOf(window.location.host);
  return window.location.href.substring(0, pos+window.location.host.length);
}

function setup() {
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
  $("*:not(#popup)").click(function() {
          $("#popup").slideUp('fast');
  });
}
