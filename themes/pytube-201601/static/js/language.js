$(window).bind( 'hashchange', function(){
  "use strict";
  var hash = location.hash;
  $('.language').hide();
  if (hash != "") {
    $(hash).show();
  }
});
$(window).trigger( 'hashchange' );
