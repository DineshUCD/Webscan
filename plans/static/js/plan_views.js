


function ajaxHandler(json, mapping, callback) {
  $.ajax({
    type: "POST",
    data: json,
    url: mapping,
    success: callback
  });
}

function select(element, url) {
  var data = {};
  if (element.id != null) {
    data[element.id] = true;
  }
  ajaxHandler(data, url, function() {
      $("#success-alert").alert();
      $("#success-alert").fadeTo(2000, 500).slideUp(500, function(){
        $("#success-alert").slideUp(500);
      }
  )});
}
