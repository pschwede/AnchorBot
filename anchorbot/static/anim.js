function getURL() {
    var pos = window.location.href.indexOf(window.location.host);
    return window.location.href.substring(0, pos+window.location.host.length);
}

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
});
