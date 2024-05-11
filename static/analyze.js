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
};

// Updates Date Filters in <div> and calls filter url
function setDateFilter(event){
    // Date Filter
    var date_filter = event.target.value
    document.getElementById("date_filter").innerHTML = date_filter

    var server_data = {
        "date": date_filter,
        "account": document.getElementById("account_filter").innerHTML,
        "category": "All",
        };

    location.href = "/analyze/?"+$.param(server_data);
};

// Updates Account Filters in <div> and calls filter url
function setAccountFilter(event){
    // Account Filter
    var account_filter = event.target.value
    document.getElementById("account_filter").innerHTML = account_filter;

    var server_data = {
        "date": document.getElementById("date_filter").innerHTML,
        "account": account_filter,
        "category": "All",
        };

    location.href = "/analyze/?"+$.param(server_data);
};

// Updates Category Filters in <div> and calls filter url
function setCategoryFilter(event){
    // Account Filter
    var category_filter = event.target.value
    document.getElementById("category_filter").innerHTML = category_filter;

    var server_data = {
        "date": "All",
        "account": "All",
        "category": category_filter
        };

    location.href = "/analyze/?"+$.param(server_data);
};