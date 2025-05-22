$(document).on('keydown', function(event) {
  // Pressing / focuses the search bar.
  if (event.key === '/' && !$(event.target).is('input')) {
    event.preventDefault(); // Prevent typing "/" in the page
    $('input[name="q"]').focus();
  }
});
// Clicking the search field selects all the existing text.
$('input[name="q"]').on('focus', function () {
  $(this).select();
});
