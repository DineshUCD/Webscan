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

function upload(handler) {
  var data = {};
  var pk = parseInt(document.getElementsByName("pk")[0].value);
  var output = Array();
  $("input:checkbox:checked").each(function() {
    output.push($(this).val());
  });
  var select = document.getElementsByName('application_id')[0];
    //.value returns the string value of the element
  var application_id = select.options[ select.selectedIndex ].value;

  var url = handler;

  data['uniform_resource_locator'] = 'http://sec-tools-01.eng.netsuite.com/threadfix/';
  data['scan'] = pk;
  data['resources'] = output;
  data['application_id'] = application_id;
  
  ajaxHandler(data, url, true);

  return true;
}   
