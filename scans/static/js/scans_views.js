$(document).ready(function() {
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

function recent() {
  $.get("/scans/list", {'recent':true}, function( data ) {
    //Remove all the rows in the table.
    $("#ongoing tbody tr").remove();

    var tbody = document.getElementById("ongoing").getElementsByTagName("tbody")[0];
    
    for (var scan = 0; scan < data.length; scan++) {
      var meta = data[scan];
      var row = tbody.insertRow(tbody.rows.length);
      
      var cell1 = row.insertCell(0);
      jQuery(cell1).text(meta['plan'] + " : " + meta['uniform_resource_locator']);

      var cell2 = row.insertCell(1);
      var diagnostic = "Scan State : " + meta['state'] + "\n";
      for (var tool = 0; tool < meta['tools'].length; tool++) {
        var item = meta['tools'][tool];
        for (var key in item) {
          diagnostic = diagnostic + key + " : " + item[key] + "\n";
        }
      } //inner for
      jQuery(cell2).text(diagnostic);

    } //for

  }).done(function() {
      $('#ongoing').dataTable();
    })
    .fail(function() {
     console.log("Failed"); 
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

  ajaxHandler(data, url, recent());

  return true;
}

setInterval(recent, 5000);
