var thumbs = $('article.list_item div.thumb a img');
$.each(thumbs, function(index, image) {
    var $img = $(image);

    if ($img.attr('src') === '/images/default_thumbnail_url.png') {
        return;
    }

    // Add the spinner icon
    $img.css("background", "url('/theme/images/loading.gif') 50% no-repeat");

    // Handle error of image download
    $img.error(function() {
        $( this ).attr( "src", "/images/default_thumbnail_url.png" );
        $( this ).css("background", "none");
    });
});
