$(document).ready(function() {
  getScanHistory();
});

function getScanHistory() {
  $.get("/scans/list/", function( data ) {
      //Remove all rows in the table.
    $("#history tbody tr").remove();

      //Find a <table> element with table id="history"
    var tbody = document.getElementById("history").getElementsByTagName("tbody")[0];

      //Loop through the JSON array Scan META objects.
    for (var scan = 0; scan < data.length; scan++) {
      var meta = data[scan];
      var row = tbody.insertRow(tbody.rows.length);
      
      //1. Plan Name
      var cell1 = row.insertCell(0);
      jQuery(cell1).text(meta['plan']);
      
      //2. Attack Point
      var cell2 = row.insertCell(1);
      jQuery(cell2).text(meta['uniform_resource_locator']);

      //3. State
      var cell3 = row.insertCell(2);
      jQuery(cell3).text(meta['state']);
  
      //4. Date Created
      var cell4 = row.insertCell(3);
      jQuery(cell4).text(meta['date']);   
 
      //5. Action 
      var cell4 = row.insertCell(4);
      duplicateDiv(meta['pk'], cell4);

    } //for

    console.log(data);
  }).done(function() {
      console.log("Done Loading!"); 
      $('#history').dataTable();
    })
    .fail(function() {
      console.log("Failed loading!");
    });
}

function duplicateDiv(divId, containerElement) {
  var original = document.getElementById("action");
  var clone = original.cloneNode(true); // "deep" clone
  clone.id = divId;
  clone.style.display=""; 
  var li = clone.querySelectorAll("ul > li")[0];
  li.onclick = function() { window.location.href = "/scans/" + divId.toString() + "/detail/" };  
  containerElement.appendChild(clone);
}
