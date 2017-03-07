//Ajax call customized for handling JSON API calls.
function ajaxHandler(json, verb, mapping, callback) {
  $.ajax({
    type: verb,
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
  
  ajaxHandler(data, "POST", url, function(response) {
    var response_alert = document.getElementById('upload-response');
    var alertText = ""; 
    console.log(response['upload_response']);
    var result = response['upload_response'];
    console.log(result);
    for (var file_upload = 0; file_upload < result.length; file_upload++) {
      alertText = alertText + "File: " + result[file_upload]['file'] + " Status: " + result[file_upload]['threadfix_response'];
    }
    response_alert.innerText = alertText;
    $('#upload-response').alert();
    $('#upload-response').fadeTo(2000, 500).slideUp(500, function() {
      $('#upload-response').slideUp(500);
    });
  });

  return false;
}   

function serialize(baseUrl, parameters) {
  var param = jQuery.param( parameters );
  var url = baseUrl + "?" + param;
  return url;
}

function download(handler) {
  var data = {};
  var output = Array();
  $("input:checkbox:checked").each(function() {
    output.push($(this).val());
  });

  data['resources'] = output;
  data['scan'] = parseInt(document.getElementsByName("pk")[0].value);
  var url = serialize(handler, data);
  window.open(url, "_blank");
}
