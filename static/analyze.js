var date_btns = document.getElementsByClassName("date_btn"); // Dropdown buttons for preset date filters (Q1, February, ...)
var account_btns = document.getElementsByClassName("account_btn"); // Dropdown buttons for Account Filter (Left Sidebar)
var category_btns = document.getElementsByClassName("category_btn"); // Dropdown buttons for Account Filter (Left Sidebar)


// Setup Function for DataTables
function initTable(){
    var table = $('#analyze_category_summary').DataTable({
        paging: false,
        ordering: false,
    });

};

// Setup event listeners for the various button onclick actions through the page
function initListeners(){
    for (let i = 0; i<account_btns.length; i++) {
        account_btns[i].addEventListener("click", setAccountFilter);
        };
    for (let i = 0; i<date_btns.length; i++) {
        date_btns[i].addEventListener("click", setDateFilter);
        };
    for (let i = 0; i<category_btns.length; i++) {
        category_btns[i].addEventListener("click", setCategoryFilter);
        };
    $('#invest_selector').on("click", setInvestFilter);
};

// Updates Date Filters in <div> and calls filter url
function setDateFilter(event){
    // Date Filter
    var date_filter = event.target.value
    document.getElementById("date_filter").innerHTML = date_filter

    var account_filter = document.getElementById("account_filter").innerHTML
    var category_filter = document.getElementById("category_filter").innerHTML
    var invest_filter = $('#invest_selector').prop('checked');

    var server_data = {
        "date": date_filter,
        "account": account_filter,
        "category": category_filter,
        "include_invest": invest_filter,
        };

    location.href = "/analyze/?"+$.param(server_data);
};

// Updates Account Filters in <div> and calls filter url
function setAccountFilter(event){
    // Account Filter
    var account_filter = event.target.value
    document.getElementById("account_filter").innerHTML = account_filter;

    var date_filter = document.getElementById("date_filter").innerHTML
    var category_filter = document.getElementById("category_filter").innerHTML
    var invest_filter = $('#invest_selector').prop('checked');

    var server_data = {
        "date": date_filter,
        "account": account_filter,
        "category": category_filter,
        "include_invest": invest_filter,
        };

    location.href = "/analyze/?"+$.param(server_data);
};

// Updates Category Filters in <div> and calls filter url
function setCategoryFilter(event){
    var category_filter = event.target.value
    document.getElementById("category_filter").innerHTML = category_filter;

    var date_filter = document.getElementById("date_filter").innerHTML
    var account_filter = document.getElementById("account_filter").innerHTML
    var invest_filter = $('#invest_selector').prop('checked');

    var server_data = {
        "date": date_filter,
        "account": account_filter,
        "category": category_filter,
        "include_invest": invest_filter,
        };

    location.href = "/analyze/?"+$.param(server_data);
};

// Updates Include Investment Filter in <div> and calls filter url
function setInvestFilter(event){
    var invest_filter = $(this).prop('checked');
    // console.log('filter clicked: ', invest_filter);

    var date_filter = document.getElementById("date_filter").innerHTML
    var account_filter = document.getElementById("account_filter").innerHTML
    var category_filter = document.getElementById("category_filter").innerHTML

    var server_data = {
        "date": date_filter,
        "account": account_filter,
        "category": category_filter,
        "include_invest": invest_filter,
        };

    location.href = "/analyze/?"+$.param(server_data);
};