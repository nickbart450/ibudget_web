// JavaScript file associated with transactions page of web app
//

var income_expense_btns = document.getElementsByClassName("income_expense_btn");
var date_btns = document.getElementsByClassName("date_btn"); // Dropdown buttons for preset date filters (Q1, February, ...)
var account_btns = document.getElementsByClassName("account_btn"); // Dropdown buttons for Account Filter (Left Sidebar)
var category_filter_btns = document.getElementsByClassName("category_btn"); // Dropdown buttons for Category Filter (Left Sidebar)
var cred_account_btns = document.getElementsByClassName("cred_account_btn"); // Dropdown buttons for Credit Account Input (Transaction Add Form)
var deb_account_btns = document.getElementsByClassName("deb_account_btn"); // Dropdown buttons for Debit Account Input (Transaction Add Form)
var category_btns = document.getElementsByClassName("cat_btn"); // Dropdown buttons for Category Input (Transaction Add Form)
var function_btns = document.getElementsByClassName("function_btn");

const today = new Date();

// Setup Function for DataTables
function initPostedTable(){
    var table = $('#budget_table_posted').DataTable({
        ajax: '/transact/_posted_table_data',
        columns: [
            { "defaultContent": "<input type='checkbox' class='select_checkbox_posted w3-check w3-margin-right'></input><button class='w3-btn w3-black'><i class='fa fa-bars'></i></button>",
            },
            { data: 'transaction_date',
              className: 'w3-center' },
            { data: 'credit_account_name',
              className: 'w3-center' },
            { data: 'debit_account_name',
              className: 'w3-center' },
            { data: 'category',
              className: 'w3-center' },
            { data: 'amount_string',
              className: 'w3-center' },
            { data: 'vendor',
              className: 'w3-center' }
        ],
        paging: false,
        scrollY: 0.205*($( window ).height())+'px',
        scrollCollapse: true,
        order: [[1, 'desc']],
        rowCallback: function(row, data, index) {
            var date_table = new Date(data['transaction_date']+ "T00:00:00");
            if (data['is_posted'] == 'checked') {}
            else {
                $(row).css('background-color', '#2E4A62');
            };
            if (date_table > today) {
                $(row).css('background-color', 'rgba(76, 115, 149, 0.36)');
                $(row).css('color', 'rgba(255, 255, 255, 0.53)');
            } else { };
        }
    });

    $('#budget_table_posted').on('click', 'button', function (e) {
        var row = $(this).parents('tr')[0];
        var data = table.row(row).data();
        // console.log(data);
        UpdateModal(data);
    });

    $('#budget_table_posted').on('click', '.select_checkbox_posted', CountSelected);

};

function initUpcomingTable(){
    var table = $('#budget_table_upcoming').DataTable({
        ajax: '/transact/_upcoming_table_data',
        columns: [
            { "defaultContent": "<input type='checkbox' class='select_checkbox_upcoming w3-check w3-margin-right'></input><button class='w3-btn w3-black'><i class='fa fa-bars'></i></button>",
            },
            { data: 'transaction_date',
              className: 'w3-center' },
            { data: 'credit_account_name',
              className: 'w3-center' },
            { data: 'debit_account_name',
              className: 'w3-center' },
            { data: 'category',
              className: 'w3-center' },
            { data: 'amount_string',
              className: 'w3-center' },
            { data: 'vendor',
              className: 'w3-center' }
        ],
        paging: false,
        scrollY: 0.55*($( window ).height())+'px',
        scrollCollapse: true,
        order: [[1, 'asc']],
        rowCallback: function(row, data, index) {
            var date_table = new Date(data['transaction_date']+ "T00:00:00");
            if (data['is_posted'] == 'checked') { }
            else {
                $(row).css('background-color', '#2E4A62');
            };
            if (date_table > today) {
                $(row).css('background-color', 'rgba(76, 115, 149, 0.36)');
                $(row).css('color', 'rgba(255, 255, 255, 0.53)');
            } else { };
        }
    });

    $('#budget_table_upcoming').on('click', 'button', function (e) {
        var row = $(this).parents('tr')[0];
        var data = table.row(row).data();
        // console.log(data);
        UpdateModal(data);
    });

    $('#budget_table_upcoming').on('click', '.select_checkbox_upcoming', CountSelected);
};

function CountSelected() {
        var selected = [];

        // iterate over class and add checked boxes to array
        $(".select_checkbox_posted").each( function (index){
            if ($(this)[0].checked) {
                selected.push(null);
            };
        });
        $(".select_checkbox_upcoming").each( function (index){
            if ($(this)[0].checked) {
                selected.push(null);
            };
        });

        // console.log(selected.length);
        if (selected.length > 0){
            document.getElementById('table_controls').style.display='inline';
        } else {
            document.getElementById('table_controls').style.display='none';
        };
};

// Update transaction modal to fill in data based on which details button is clicked
function UpdateModal(data) {
    // Fill data into modal
    document.getElementById('details_modal_id').innerHTML = "TRANSACTION EDIT - "+data['transaction_id'];

    var update_action = document.getElementById('details_modal_form').name + "?transaction_id=";
    document.getElementById('details_modal_form').action = update_action+data['transaction_id'];
    document.getElementById('details_modal_delete').onclick = function() {delete_transactions(data['transaction_id'])};

    document.getElementById('details_modal_trans_date').value = data['transaction_date'];
    document.getElementById('details_modal_post_date').value = data['posted_date'];
    document.getElementById('details_modal_credit_account').value = data['credit_account_name'];
    document.getElementById('details_modal_debit_account').value = data['debit_account_name'];
    document.getElementById('details_modal_amount').value = data['amount'];
    document.getElementById('details_modal_category').value = data['category'];
    document.getElementById('details_modal_description').value = data['description'];

    if (data["is_posted"] === "checked") {
        document.getElementById('details_modal_posted').checked = true;
    } else {
        document.getElementById('details_modal_posted').checked = false;
    };

    document.getElementById('details_modal_vendor').value = data['vendor'];

    // Show modal
    document.getElementById('details_modal').style.display = 'block';
};

// LISTENERS
// Setup event listeners for the various button onclick actions through the page
function initListeners(){
    for (let i = 0; i<income_expense_btns.length; i++) {
        income_expense_btns[i].addEventListener("click", setExpenseIncomeFilter);
        };
    for (let i = 0; i<account_btns.length; i++) {
        account_btns[i].addEventListener("click", setAccountFilter);
        };
    for (let i = 0; i<category_filter_btns.length; i++) {
        category_filter_btns[i].addEventListener("click", setCategoryFilter);
        };
    for (let i = 0; i<deb_account_btns.length; i++) {
        deb_account_btns[i].addEventListener("click", setDebAccount);
        };
    for (let i = 0; i<cred_account_btns.length; i++) {
        cred_account_btns[i].addEventListener("click", setCredAccount);
        };
    for (let i = 0; i<date_btns.length; i++) {
        date_btns[i].addEventListener("click", setDateFilter);
        };
    for (let i = 0; i<category_btns.length; i++) {
        category_btns[i].addEventListener("click", setCategory);
        };
    for (let i = 0; i<function_btns.length; i++) {
        function_btns[i].addEventListener("click", onClickFunction);
        };
};

// Updates Date Filters in <div> and calls filter url
function setExpenseIncomeFilter(event){
    var income_expense_filter = event.target.value;
    // console.log('filter clicked: ',  income_expense_filter);

    var date_start = null;
    var date_end = null;

    var server_data = {"income_expense": income_expense_filter,
        "date": document.getElementById("date_filter").innerHTML,
        "account": document.getElementById("account_filter").innerHTML,
        "category": document.getElementById("category_filter").innerHTML,
        "date_start": date_start,
        "date_end": date_end,
        };

    location.href = "/transact/?"+$.param(server_data);

};

// Updates Date Filters in <div> and calls filter url
function setDateFilter(event){
    // Date Filter
    var date_filter = event.target.value
    // console.log('Setting Date Filter to: ', date_filter)
    document.getElementById("date_filter").innerHTML = date_filter

    // Income/Expense Filter
    var income_expense_radios = document.getElementsByClassName("income_expense_btn");
    for (let i = 0; i<income_expense_radios.length; i++) {
        // console.log(income_expense_radios[i].value, income_expense_radios[i].checked)
        if (income_expense_radios[i].checked) {
            var income_expense_select = income_expense_radios[i].value;
            // console.log('income_expense_select', income_expense_select);
        };
    };

    var date_start = null;
    var date_end = null;

    var server_data = {"income_expense": income_expense_select,
        "date": date_filter,
        "account": document.getElementById("account_filter").innerHTML,
        "category": document.getElementById("category_filter").innerHTML,
        "date_start": date_start,
        "date_end": date_end,
        };

    location.href = "/transact/?"+$.param(server_data);
};

// Updates Account Filters in <div> and calls filter url
function setAccountFilter(event){
    // Account Filter
    var account_filter = event.target.value
    // console.log('Setting Account Filter to: ', account_filter)
    document.getElementById("account_filter").innerHTML = account_filter;

    // Income/Expense Filter
    var income_expense_radios = document.getElementsByClassName("income_expense_btn");
    for (let i = 0; i<income_expense_radios.length; i++) {
        if (income_expense_radios[i].checked)
            var income_expense_select = income_expense_radios[i].value;
            console.log('income_expense_select: ', income_expense_select);
        };

    var date_start = null;
    var date_end = null;

    var server_data = {"income_expense": income_expense_select,
        "date": document.getElementById("date_filter").innerHTML,
        "account": account_filter,
        "category": document.getElementById("category_filter").innerHTML,
        "date_start": date_start,
        "date_end": date_end,
        };

    location.href = "/transact/?"+$.param(server_data);
};

// Updates Category Filters in <div> and calls filter url
function setCategoryFilter(event){
    // Category Filter
    var category_filter = event.target.value
    // console.log('Setting Category Filter to: ', category_filter)
    document.getElementById("category_filter").innerHTML = category_filter;

    // Income/Expense Filter
    var income_expense_radios = document.getElementsByClassName("income_expense_btn");
    for (let i = 0; i<income_expense_radios.length; i++) {
        if (income_expense_radios[i].checked)
            var income_expense_select = income_expense_radios[i].value;
            console.log('income_expense_select: ', income_expense_select);
        };

    var date_start = null;
    var date_end = null;

    var server_data = {"income_expense": income_expense_select,
        "date": document.getElementById("date_filter").innerHTML,
        "account": document.getElementById("account_filter").innerHTML,
        "category": category_filter,
        "date_start": date_start,
        "date_end": date_end,
        };

    location.href = "/transact/?"+$.param(server_data);
};

// Add Transaction Form - Account Dropdowns <div> updates
function setDebAccount(event){
    console.log('Setting Deb Account Input to: ', event.target.value);
    document.getElementById("deb_accnt_input").value = event.target.value;

    var deb_account_modal_inputs = document.getElementsByClassName("deb_accnt_input_modal")
    for (let i = 0; i<deb_account_modal_inputs.length; i++) {
        deb_account_modal_inputs[i].value = event.target.value;
    };
};
function setCredAccount(event){
    console.log('Setting Cred Account Input to: ', event.target.value);
    document.getElementById("cred_accnt_input").value = event.target.value;

    var cred_account_modal_inputs = document.getElementsByClassName("cred_accnt_input_modal")
    for (let i = 0; i<cred_account_modal_inputs.length; i++) {
        cred_account_modal_inputs[i].value = event.target.value;
    };
};

// Add Transaction Form - Category Dropdown  <div> update
function setCategory(event){
    console.log('Setting Category Input to: ', event.target.value)
    document.getElementById("cat_input").value = event.target.value;

    var cat_modal_inputs = document.getElementsByClassName("cat_input_modal")
    for (let i = 0; i<cat_modal_inputs.length; i++) {
        cat_modal_inputs[i].value = event.target.value;
    };
};

// Transaction edit functions
function delete_transactions(id_array){
    if (confirm('Confirm DELETE transaction(s): '+id_array+'?')){
        console.log("/transact/delete_transaction?transaction_id="+id_array)
        location.href = "/transact/delete_transaction?transaction_id="+id_array;
    } else {
        console.log("Delete Cancelled")
    }
};

function duplicate_transactions(id_array){
    if (confirm('Confirm duplicate transaction(s): '+id_array+'?')){
        console.log("/transact/duplicate_transaction?transaction_id="+id_array)
        location.href = "/transact/duplicate_transaction?transaction_id="+id_array;
    } else {
        console.log("Duplicate Cancelled")
    }
};

function post_transactions(id_array){
    if (confirm('Confirm mark transaction(s): '+id_array+' posted?')){
        console.log("/transact/post_transaction?transaction_id="+id_array)
        location.href = "/transact/post_transaction?transaction_id="+id_array;
    } else {
        console.log("Duplicate Cancelled")
    }
};

// Multi-Select Function Buttons
function onClickFunction(event){
    console.log('Function Clicked: ', event.target.id)

    var posted_table = $('#budget_table_posted').DataTable();
    var upcoming_table = $('#budget_table_upcoming').DataTable();
    var selected = [];

    $(".select_checkbox_posted").each( function (index){
        if ($(this)[0].checked) {
            // console.log($(this));

            var row = $(this).parents('tr')[0];
            var data = posted_table.row(row).data();
            // console.log(data['transaction_id']);
            selected.push(data['transaction_id']);

        };
    });

    $(".select_checkbox_upcoming").each( function (index){
        if ($(this)[0].checked) {
            // console.log($(this));

            var row = $(this).parents('tr')[0];
            var data = upcoming_table.row(row).data();
            // console.log(data['transaction_id']);
            selected.push(data['transaction_id']);

        };
    });

    // console.log(selected);
    if (event.target.id === 'delete'){
        delete_transactions(selected);

    } else if (event.target.id === 'duplicate') {
        duplicate_transactions(selected);

    } else if (event.target.id === 'posted') {
        post_transactions(selected);

    }
};
