$(document).ready(function() {
  $('#ongoing').dataTable();
  $('#selected').dataTable();
});

//Ajax call customized for handling JSON API calls.
function ajaxHandler(json, mapping, callback) {
  $.ajax({
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify(json),
    dataType: 'json',
    url: mapping,
    success: callback
  });
}

function launch(element) {
  var data = {};
  var pk = parseInt(element.id);

  if (isNaN(pk)) {
    return false;
  }
  var url = '/scans/list/';
  data['plan'] = pk;
  data['uniform_resource_locator'] = document.getElementById('uniform_resource_locator').value;

  ajaxHandler(data, url, true);

  return true;
}
