var $thumbs = $('article.list_item div.thumb a img');
$.each($thumbs, function(index, image) {
    var $image = $(image);
    var $downloadingImage = $("img");
    $downloadingImage.load(function(){
        console.log($(this).attr("src"));
        $image.attr("src", $(this).attr("src"));
    });
    $downloadingImage.attr("src", $image.attr('data-src'));
});

