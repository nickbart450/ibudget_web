// Set objects
var income_expense_btns = document.getElementsByClassName("income_expense_btn");
var date_btns = document.getElementsByClassName("date_btn"); // Dropdown buttons for preset date filters (Q1, February, ...)
var account_btns = document.getElementsByClassName("account_btn"); // Dropdown buttons for Account Filter (Left Sidebar)
var category_filter_btns = document.getElementsByClassName("category_btn"); // Dropdown buttons for Category Filter (Left Sidebar)
var cred_account_btns = document.getElementsByClassName("cred_account_btn"); // Dropdown buttons for Credit Account Input (Transaction Add Form)
var deb_account_btns = document.getElementsByClassName("deb_account_btn"); // Dropdown buttons for Debit Account Input (Transaction Add Form)
var category_btns = document.getElementsByClassName("cat_btn"); // Dropdown buttons for Category Input (Transaction Add Form)

// Setup Function for DataTables
function initDataTables(raw_data){
    const today = new Date();
    $('#budget_table').DataTable({
        paging: false,
        scrollY: 0.805*($( window ).height())+'px',
        scrollCollapse: true,
        order: [[1, 'asc']],
        rowCallback: function(row, data, index) {
            var date_table = new Date(raw_data[index]['transaction_date']+ "T00:00:00");
            // console.log(date_table, today)
            if (raw_data[index]['is_posted'] == 'checked') {}
            else {
                $(row).css('background-color', '#2E4A62');
            };
            if (date_table > today) {
                $(row).css('background-color', 'rgba(76, 115, 149, 0.36)');
                $(row).css('color', 'rgba(255, 255, 255, 0.53)');
            } else { };
        }
    });
};

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
};

// Called when the Delete button is clicked on "Details" modal
function delete_transaction_from_modal(transaction_id){
    if (confirm('Confirm DELETE?')){
        console.log("/transact/delete_transaction?transaction_id="+transaction_id)
        location.href = "/transact/delete_transaction?transaction_id="+transaction_id;
    } else {
        console.log("Delete Cancelled")
    }
};

// Updates Date Filters in <div> and calls filter url
function setExpenseIncomeFilter(event){
    var income_expense_filter = event.originalTarget.value;
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

    location.href = "/transact/data?"+$.param(server_data);

};

// Updates Date Filters in <div> and calls filter url
function setDateFilter(event){
    // Date Filter
    var date_filter = event.originalTarget.value
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

    location.href = "/transact/data?"+$.param(server_data);
};

// Updates Account Filters in <div> and calls filter url
function setAccountFilter(event){
    // Account Filter
    var account_filter = event.originalTarget.value
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

    location.href = "/transact/data?"+$.param(server_data);
};

// Updates Category Filters in <div> and calls filter url
function setCategoryFilter(event){
    // Category Filter
    var category_filter = event.originalTarget.value
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

    location.href = "/transact/data?"+$.param(server_data);
};

// Add Transaction Form - Account Dropdowns <div> updates
function setDebAccount(event){
    console.log('Setting Deb Account Input to: ', event.originalTarget.value);
    document.getElementById("deb_accnt_input").value = event.originalTarget.value;

    var deb_account_modal_inputs = document.getElementsByClassName("deb_accnt_input_modal")
    for (let i = 0; i<deb_account_modal_inputs.length; i++) {
        deb_account_modal_inputs[i].value = event.originalTarget.value;
    };
};
function setCredAccount(event){
    console.log('Setting Cred Account Input to: ', event.originalTarget.value);
    document.getElementById("cred_accnt_input").value = event.originalTarget.value;

    var cred_account_modal_inputs = document.getElementsByClassName("cred_accnt_input_modal")
    for (let i = 0; i<cred_account_modal_inputs.length; i++) {
        cred_account_modal_inputs[i].value = event.originalTarget.value;
    };
};

// Add Transaction Form - Category Dropdown  <div> update
function setCategory(event){
    console.log('Setting Category Input to: ', event.originalTarget.value)
    document.getElementById("cat_input").value = event.originalTarget.value;

    var cat_modal_inputs = document.getElementsByClassName("cat_input_modal")
    for (let i = 0; i<cat_modal_inputs.length; i++) {
        cat_modal_inputs[i].value = event.originalTarget.value;
    };
};