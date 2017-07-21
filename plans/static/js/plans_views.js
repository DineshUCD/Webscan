$(document).ready(function() {
  $('#planning').dataTable();
  $('#group').dataTable();
});

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

function createCli(url) {
  $('#extraTool').load(url);
}

function updateCli(url) {
  createCli(url);
  $('#cli').modal('show');
}

function createPlan(url) {
  $('#planConfiguration').load(url);
}

function updatePlan(url) {
  createPlan(url);
  $('#myModal').modal('show');
}

function remove(element, url) {
  ajaxHandler(null, url, true);
  $(element).closest('tr').remove();
}
