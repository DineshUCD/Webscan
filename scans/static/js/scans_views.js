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

var statusColor = {
  'PENDING': 'text-muted',
  'STARTED': 'text-info',
  'SUCCESS': 'text-success',
  'FAILURE': 'text-danger'
}

function createElement(element, addClass, text) {
  var creation = document.createElement('p');
  creation.className = addClass;
  creation.innerText = text;
  return creation;
}

function recent() {
  $.get("/scans/list", {'recent':true}, function( data ) {
    //Remove all the rows in the table.
    $("#ongoing tbody tr").remove();

    //Get the table body of the scan status report table.
    var tbody = document.getElementById("ongoing").getElementsByTagName("tbody")[0];
    
    //For each recent scan (within t time of current date & time)
    for (var scan = 0; scan < data.length; scan++) {
      var meta = data[scan];
      var row = tbody.insertRow(tbody.rows.length);
      
      //1. Plan Information
      var cell1 = row.insertCell(0);
      jQuery(cell1).text(meta['plan'] + " : " + meta['uniform_resource_locator']);

      //2. Overall status and tool status
      var cell2 = row.insertCell(1);
        //Overall Status
 
      cell2.appendChild(createElement('p', "lead", "Scan Status: "));
      cell2.appendChild(createElement('p', statusColor[meta['state']], meta['state'])); 

        //For each tool, list the status.
      for (var tool = 0; tool < meta['tools'].length; tool++) {
        var item = meta['tools'][tool];
        for (var key in item) {
          cell2.appendChild(createElement('p', "lead", key + ":"));
          cell2.appendChild(createElement('p', statusColor[item[key]], item[key]));
        }
      } //inner for
    } //for
    $('#ongoing').dataTable();

  }).done(function() {
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
