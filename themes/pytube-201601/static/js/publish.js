$('#js-publish-btn').click(function onClick() {
  "use strict";

  var url = $('#publisher_url').val();

  var data = {
    data_file: $('#data_file').val(),
    publish_key: $('#publish_key').val()
  };

  $.post({
    url: url,
    data: data,
  }).done(function onDone(res) {
    if (res.result === 'ok') {
      alert('Publish request recieved!');
      $('#publishModal').modal('hide');
    } else if (res.result === 'failure') {
      alert('Publish request failed: ' + res.msg);
    }
  }).fail(function onFail() {
    alert('Communication error. Please try again another time.');
  });
});

