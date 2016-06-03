var thumbs = $('article.list_item div.thumb a img');
$.each(thumbs, function(index, image) {
    // Add the spinner icon
    $( image ).css("background", "url('/theme/images/loading.gif') 50% no-repeat");

    // Handle error of image download
    $(image).error(function() {
        $( this ).attr( "src", "/images/default_thumbnail_url.png" );
        $( this ).css("background", "none");
    });
});
