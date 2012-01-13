show_start = function() {
}


$('document').ready(function() {
    $('.issue2').hover(
            function() {
                $(this).find('.small').slideDown('fast', function() {
                });
            },
            function() {
                $(this).find('.small').slideUp('fast', function() {});
            }
        );
    $('.issue2').click(
            function() {
                $(this).fadeOut('fast');
            }
        );
});
