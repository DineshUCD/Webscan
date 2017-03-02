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

function upload() {
  var data = {};
  var pk = parseInt(document.getElementsByName("pk")[0].value);
  var output = Array();
  $("input:checkbox:checked").each(function() {
    output.push($(this).val());
  });

  var url = '/uploads/list/';

  data['uniform_resource_locator'] = 'http://sec-tools-01.eng.netsuite.com/threadfix/';
  data['scan'] = pk;
  data['resources'] = output;
  
  ajaxHandler(data, url, true);

  return true;
}   
