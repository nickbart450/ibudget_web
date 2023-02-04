// Setup Function for DataTables
function initDataTables(){
    $('#account_value_table').DataTable({
        paging: false,
        scrollY: 0.65*($( window ).height())+'px',
        scrollCollapse: true,
        order: [[1, 'asc']],
        rowCallback: function(row, data, index) {
            if (data[3] > 1000) {
                $(row).find('td:eq(3)').css('color', 'blue');
            } else if (data[3] <= 0) {
                $(row).find('td:eq(3)').css('background-color', 'red');
            }
        }
    });
};

function dropdownFunction(id) {
  var x = document.getElementById(id);
  if (x.className.indexOf("w3-show") == -1) {
  x.className += " w3-show";
  } else {
    x.className = x.className.replace(" w3-show", "");
  }
};