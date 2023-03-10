String.prototype.format = function () {
  var i = 0, args = arguments;
  return this.replace(/{}/g, function () {
    return typeof args[i] != 'undefined' ? args[i++] : '';
  });
};


// Setup Function for DataTables
var checking_column = 5

function initDataTables(){
    $('#account_value_table').DataTable({
        paging: false,
        scrollY: 0.666*($( window ).height())+'px',
        scrollCollapse: true,
        order: [[1, 'asc']],
        rowCallback: function(row, data, index) {
            if (data[checking_column] > 1000) {
                $(row).find('td:eq({})'.format(checking_column)).css('color', 'blue');
            } else if (data[checking_column] <= 0) {
                $(row).find('td:eq({})'.format(checking_column)).css('background-color', 'red');
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