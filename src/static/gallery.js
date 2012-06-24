var offset = 0;
var vert_num = 3;
var hori_num = 5;  // unused

function new_article(article) {
  // Build up keyword button list
  buttons = $("<div/>", {
    'class': 'small',
  }).append(
    $("<span/>", {
      style: "font-size:50%",
      html: "Release: "+Humanize.naturalDay(parseInt(article.datestr))
    })
  ).append(
    $("<div/>", {
      style: "font-size:50%; width: 100%;",
      html: "Why do you want to read this?"
    })
  );
  $.each(article.keywords, function(l, key) {
      $("<a/>", {
        'class': "button",
        html: key.word,
        title: "/read/"+article.ID,
        style: "margin-left:5pt;"
      }).click(function() {
          $.getJSON('/like/keyword/by/id/'+key.ID, function() {
              window.location = "/key/"+key.word;
          });
      }).appendTo(buttons);
  });
  // append article to gallery of keyword
  return $("<div/>", {
    'class': 'issue2',
    id: article.ID,
    style: "background-image: url("+article.image.filename+");"
  }).append(
    $("<h2/>", {
      'class': 'issue_head',
      html: article.title
    })
  ).append(buttons);
}


function load(callback) {
    done = false;
    contained = $("#content .issue2");
    $.getJSON("/json/top/articles/"+offset+"/"+(vert_num*hori_num),
        function(data) {
            contained.each(function(i, iss) {
                $.getJSON("/hate/article/by/id/"+iss.id);
            });
            contained.remove();
            $.each(data.articles, function(i, art) {
                new_article(art).appendTo("#content", function() {
                    $(this).fadeIn("fast");
                    done = true;
                });
            });
        });
    offset += 1;
    if(callback && done) callback();
}


$('document').ready(function() {
    setup();
    load();
    $("#container").append(
        $("<div/>", {
            style: "width:100%;text-align:center;"
        }).append(
            $("<a/>", {
                html: "MOAR",
                "class": "more button",
            })
        ).click(function() {
            button = $(this);
            button.fadeOut("fast", function() {
                load(function() {button.fadeIn("slow");});
            });
        }));
});
