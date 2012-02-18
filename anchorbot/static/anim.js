function getURL() {
    var pos = window.location.href.indexOf(window.location.host);
    return window.location.href.substring(0, pos+window.location.host.length);
}

var otheroff = 0;
var offset = 0;
var offx = 0;
var offy = 0;

function load_gallery(offset) {
    $.getJSON('/gallery/key/offset/'+offset+',0', function(data) {
        $.each(data.keywords, function(j, k) {
            if($("#container #"+k.word).length==0) {
                $('<div/>', {
                    'class': "gallery",
                    id: k.word,
                    html: '<a href="/key/'+k.word+'"><h1>'+k.word+'</h1></a>'
                }).appendTo("#container").fadeIn();
            }
        });
        $.each(data.articles, function(i, a) {
            var buttons = [];
            $.each(a.keywords, function(j, k) {
                buttons.push('<a class="button" href="/key/'+k.word+'">'+k.word+'</a>');
            });
            $.each(a.keywords, function(j, k) {
                if($("#"+a.ID).length == 0
                        && $("#container #"+k.word+" .issue2").length<5) {
                    $("<div/>", {
                        'class': 'issue2',
                        id: a.ID,
                        style: "background-image: url("+a.image.filename+");",
                        html: '<h2 class="issue_head">'+a.title+'</h2>'
                    }).append('<div class="small"><div class="tags">'+buttons.join(" ")+'</div></div>').appendTo("#container #"+k.word);
                    $("#"+k.word);
                }
            });
        });
    });
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

    load_gallery(offset);
    offset++;
    load_gallery(offset);
    offset++;

    $(window).scroll(function() {
        if($(window).scrollTop() >= $(document).height() - $(window).height() - 40) {
            load_gallery(offset);
            offset += 1;
        }
    });
});
