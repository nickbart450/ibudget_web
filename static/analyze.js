var date_btns = document.getElementsByClassName("date_btn"); // Dropdown buttons for preset date filters (Q1, February, ...)
var account_btns = document.getElementsByClassName("account_btn"); // Dropdown buttons for Account Filter (Left Sidebar)


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
};

// Updates Date Filters in <div> and calls filter url
function setDateFilter(event){
    // Date Filter
    var date_filter = event.originalTarget.value
    // console.log('Setting Date Filter to: ', date_filter)
    document.getElementById("date_filter").innerHTML = date_filter

    var date_start = null;
    var date_end = null;

    var server_data = {
        "date": date_filter,
        "account": document.getElementById("account_filter").innerHTML,
        "date_start": date_start,
        "date_end": date_end,
        };

    location.href = "/analyze/?"+$.param(server_data);
};

// Updates Account Filters in <div> and calls filter url
function setAccountFilter(event){
    // Account Filter
    var account_filter = event.originalTarget.value
    // console.log('Setting Account Filter to: ', account_filter)
    document.getElementById("account_filter").innerHTML = account_filter;

    var date_start = null;
    var date_end = null;

    var server_data = {
        "date": document.getElementById("date_filter").innerHTML,
        "account": account_filter,
        "date_start": date_start,
        "date_end": date_end,
        };

    location.href = "/analyze/?"+$.param(server_data);
};