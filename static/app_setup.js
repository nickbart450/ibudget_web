// UI show/hide functions
function myFunc(id) {
    var x = document.getElementById("setup_"+id);
    var all = document.getElementsByClassName("setup_hidden");

    if (x.className.indexOf("w3-show") == -1) {
      for (let i = 0; i < all.length; i++) {
        all[i].className = all[i].className.replace(" w3-show", "");
      }
      x.className += " w3-show";

    } else {
      x.className = x.className.replace(" w3-show", "");

    }

    // Recalculate column widths to fix bug when hiding/showing DataTables
    $($.fn.dataTable.tables(true)).DataTable().columns.adjust();
};


// jQuery ajax form submissions
$(document).on('submit','#Home_individual_settings_form',function(e) {
    console.log('submitting home settings');
    e.preventDefault();

    var form_data = $(this).serialize();
    $.ajax({
        type:'POST',
        url:'/setup/update/',
        data:'type=home&'+form_data,
        success:function() {
           // alert('Saved');
        }
    });
});

$(document).on('submit','#Personal_individual_settings_form',function(e) {
    console.log('submitting personal settings');
    e.preventDefault();

    $.ajax({
        type:'POST',
        url:'/setup/update/',
        data:{
            type: 'personal',
            average_monthly_expend: $("#average_monthly_expend").val(),
            pay_day : $("#pay_day").val(),
            first_pay_day: $("#first_pay_day").val(),
            retirement_tax_rate: $("#retirement_tax_rate").val()
        },
        success:function() {
           // alert('Saved');
        }
    });
});

$(document).on('submit','#Database_individual_settings_form',function(e) {
    console.log('submitting database file settings');
    e.preventDefault();

    $.ajax({
        type:'POST',
        url:'/setup/update/',
        data:{
            type: 'database',
            live: $("#live").val(),
            home : $("#home").val()
        },
        success:function() {
           // alert('Saved');
        }
    });
});


// Category Settings
// -- DataTable Setup Function
function initCategoryTable(){
    var table = $('#Category_table').DataTable({
        ajax: '/setup/_category_table_data/',
        columns: [
            { data: 'cat_id',
              title: 'ID',
              className: 'w3-center' },
            { data: 'category_name',
              title: 'Name',
              render: function (data, type, row, meta) {
                return "<input type='text' name='category_name' style='width:100%;' value='" + data + "'>";
              },
              className: 'w3-center' },
            { data: 'description',
              render: function (data, type, row, meta) {
                if (!data) {
                  data = "";
                };
                return "<input type='text' name='description' style='width:100%;' value='" + data + "'>";
              },
              title: 'Description',
              className: 'w3-center' },
            { data: 'cat_id',
              title: 'Functions',
              className: 'w3-center',
              render: function (data, type, row, meta) {
                return "<button type='button' id='" + data + "' onclick='delete_category_entry(" + data + ")' class='w3-btn w3-red w3-round'><i class='fa fa-minus'></i></button>";
              }
            }
        ],
        paging: false,
        scrollY: 0.75*($( window ).height())+'px',
        scrollCollapse: true,
        order: [[0, 'asc']],
        searching: false
    });
};

// -- Handle Form Submission
$(document).on('submit','#Category_table_settings_form',function(e) {
    console.log('submitting category table settings');
    e.preventDefault();

    var data = []
    var table = $('#Category_table').DataTable()
    table.rows().every(function(){
        // console.log('cat_id', this.data()['cat_id']);  // Existing data when table was loaded
        // console.log('category_name', $(table.cell(this.index(), 1).node()).find('input').val());  // 1: category_name
        // console.log('description', $(table.cell(this.index(), 2).node()).find('input').val());  // 2: description

        data.push({
            'cat_id': this.data()['cat_id'],
            'category_name': $(table.cell(this.index(), 1).node()).find('input').val(),
            'description': $(table.cell(this.index(), 2).node()).find('input').val()
        })
    });

    console.log(data);

    $.ajax({
        type:'POST',
        url:'/setup/update/',
        data: JSON.stringify(data),
        contentType: 'application/json',
        success:function() {
            // alert('Saved');
            $('#Category_table').DataTable().ajax.reload();

        }
    });
});

// -- Delete item
function delete_category_entry(item){
    if (confirm('Confirm DELETE?')){
        $.ajax({
            type:'POST',
            url:'/setup/delete/',
            data:{
                type: 'category',
                id: item
            },
            success:function() {
                // alert('Saved');
                $('#Category_table').DataTable().ajax.reload();
            }
        });

    } else {
        console.log("Delete Cancelled")
    };
};

// -- New Item
$(document).on('submit','#setup_new_modal_Category',function(e) {
    console.log('Adding new category')
//    console.log(e.target);
    e.preventDefault();

    $.ajax({
        type:'POST',
        url:'/setup/new/',
        data:{
            cat_id: $("#cat_id").val(),
            category_name : $("#category_name").val(),
            description : $("#description").val()
        },
        success:function() {
            alert('Saved');
            document.getElementById('setup_new_modal_Category').style.display='none';
            $('#Category_table').DataTable().ajax.reload();
        }
    });
});


// Account Settings
// -- DataTable Setup Function
function initAccountTable(){
    var table = $('#Account_table').DataTable({
        ajax: '/setup/_account_table_data/',
        columns: [
            { data: 'account_id',
              title: 'ID',
              className: 'w3-center' },
            { data: 'account_name',
              title: 'Name',
              render: function (data, type, row, meta) {
                return "<input type='text' name='account_name' style='width:100%;' value='" + data + "'>";
              },
              className: 'w3-center' },
            { data: 'account_type',
              render: function (data, type, row, meta) {
                if (!data) {
                  data = "";
                };
                return "<input type='text' name='description' style='width:100%;' value='" + data + "'>";
              },
              title: 'Account Type',
              className: 'w3-center' },
            { data: 'transaction_type',
              render: function (data, type, row, meta) {
                if (!data) {
                  data = "";
                };
                return "<input type='text' name='description' style='width:100%;' value='" + data + "'>";
              },
              title: 'Transaction Type',
              className: 'w3-center' },
            { data: 'starting_value',
              render: function (data, type, row, meta) {
                if (!data) {
                  data = 0;
                };
                return "<input type='text' name='description' style='width:100%;' value='" + data + "'>";
              },
              title: 'Starting Value',
              className: 'w3-center' },
            { data: 'account_id',
              title: 'Functions',
              className: 'w3-center',
              render: function (data, type, row, meta) {
                return "<button type='button' id='" + data + "' onclick='delete_account_entry(" + data + ")' class='w3-btn w3-red w3-round'><i class='fa fa-minus'></i></button>";
              }
            }
        ],
        paging: false,
        scrollY: 0.75*($( window ).height())+'px',
        scrollCollapse: true,
        order: [[0, 'asc']],
        searching: false
    });
};

// -- Handle Form Submission
$(document).on('submit','#Account_table_settings_form',function(e) {
    console.log('submitting account table settings');
    e.preventDefault();

    var data = []
    var table = $('#Account_table').DataTable()
    table.rows().every(function(){
        // console.log('account_id', this.data()['account_id']);  // Existing data when table was loaded
        // console.log('account_name', $(table.cell(this.index(), 1).node()).find('input').val());  // 1: account_name
        // console.log('account_type', $(table.cell(this.index(), 2).node()).find('input').val());  // 2: account_type

        data.push({
            'account_id': this.data()['account_id'],
            'account_name': $(table.cell(this.index(), 1).node()).find('input').val(),
            'account_type': $(table.cell(this.index(), 2).node()).find('input').val(),
            'transaction_type': $(table.cell(this.index(), 3).node()).find('input').val(),
            'starting_value': $(table.cell(this.index(), 4).node()).find('input').val(),
        })
    });

    console.log(data);

    $.ajax({
        type:'POST',
        url:'/setup/update/',
        data: JSON.stringify(data),
        contentType: 'application/json',
        success:function() {
            // alert('Saved');
            $('#Category_table').DataTable().ajax.reload();

        }
    });
});

// -- Delete item
function delete_account_entry(item){
    if (confirm('Confirm DELETE?')){
        $.ajax({
            type:'POST',
            url:'/setup/delete/',
            data:{
                type: 'account',
                id: item
            },
            success:function() {
               // alert('Saved');
               $('#Account_table').DataTable().ajax.reload();
            }
        });

    } else {
        console.log("Delete Cancelled")
    };
};

// -- New Item
$(document).on('submit','#setup_new_modal_Account',function(e) {
    console.log('Adding new account')
    console.log(e.target);
    e.preventDefault();

    $.ajax({
        type:'POST',
        url:'/setup/new/',
        data:{
            account_id: $("#account_id").val(),
            account_name : $("#account_name").val(),
            transaction_type : $("#transaction_type").val(),
            account_type : $("#account_type").val(),
            starting_value : $("#starting_value").val(),
        },
        success:function() {
            alert('Saved');
            document.getElementById('setup_new_modal_Account').style.display='none';
            $('#Account_table').DataTable().ajax.reload();
        }
    });
});

// Links Settings
// -- DataTable Setup Function
function initLinksTable(){
    var table = $('#Links_list').DataTable({
        ajax: '/setup/_links_table_data/',
        columns: [
            { data: 'link_id',
              title: 'ID',
              className: 'w3-center',
              },
            { data: 'link_url',
              title: 'Link',
              render: function (data, type, row, meta) {
                return "<input type='text' name='link_url' style='width:100%;' value='" + data + "'>";
              },
              className: 'w3-input w3-center' },
            { data: 'link_id',
              title: 'Functions',
              className: 'w3-center',
              render: function (data, type, row, meta) {
                return "<button type='button' id='" + data + "' onclick='delete_Links_entry(" + data + ")' class='w3-btn w3-red w3-round'><i class='fa fa-minus'></i></button>";
              }
            }
        ],
        paging: false,
        scrollY: 0.75*($( window ).height())+'px',
        scrollCollapse: true,
        order: [[0, 'asc']],
        searching: false
    });
};

// -- Handle Form Submission for Update
$(document).on('submit','#Links_list_settings_form',function(e) {
    // console.log('submitting Links table settings');
    e.preventDefault();

    var data = []
    var table = $('#Links_list').DataTable()
    table.rows().every(function(){
    // console.log('link_id', this.data()['link_id']);  // Existing data when table was loaded
    // console.log('link_url', $(table.cell(this.index(), 1).node()).find('input').val());
    // console.log('pushing data')
        data.push({
            'link_id': this.data()['link_id'],
            'link_url': $(table.cell(this.index(), 1).node()).find('input').val(),
        });
    });
    // console.log(data);

    $.ajax({
        type:'POST',
        url:'/setup/update/',
        data: JSON.stringify(data),
        contentType: 'application/json',
        success:function() {
            alert('Saved');
            $('#Links_list').DataTable().ajax.reload();

        }
    });
});

// -- New Item
$(document).on('submit','#setup_new_modal_Links_list',function(e) {
//    console.log('Adding new Link');
//    console.log($("#list_Links").val());
    e.preventDefault();

    $.ajax({
        type:'POST',
        url:'/setup/new/',
        data:{
            link_url: $("#list_Links").val(),
        },
        success:function() {
            $("#list_Links").val('')
            alert('Saved');
            document.getElementById('setup_new_modal_Links_list').style.display='none';
            $('#Links_list').DataTable().ajax.reload();
        }
    });
});

// -- Delete item
function delete_Links_entry(item){
    if (confirm('Confirm DELETE?')){
        $.ajax({
            type:'POST',
            url:'/setup/delete/',
            data:{
                type: 'Links',
                id: item
            },
            success:function() {
                alert('Saved');
                $('#Links_list').DataTable().ajax.reload();
            }
        });

    } else {
        console.log("Delete Cancelled")
    };
};
