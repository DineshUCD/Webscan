function ajaxHandler(json, mapping) {
  var status = false;
  $.ajax({
    type: "POST",
    data: json,
    url: mapping,
    success: function() { status = true; },
  });
  return status;
}

function select(element, url) {
  var data = {};
  if (element.id != null) {
    data[element.id] = true;
  }
  var result = ajaxHandler(data, url);
  
}
