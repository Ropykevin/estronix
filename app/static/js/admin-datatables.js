document.addEventListener("DOMContentLoaded", function () {
    if (typeof DataTable === "undefined") {
        return;
    }

    document.querySelectorAll("table.admin-datatable").forEach(function (table) {
        var defaultSort = table.dataset.defaultSort;
        var options = {
            pageLength: 25,
            lengthMenu: [10, 25, 50, 100, 250],
            order: defaultSort ? JSON.parse(defaultSort) : [],
            columnDefs: [
                { targets: "no-sort", orderable: false, searchable: false },
            ],
            language: {
                search: "Filter:",
                searchPlaceholder: "Type to search...",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                infoEmpty: "No entries to show",
                emptyTable: "No records found",
                zeroRecords: "No matching records found",
            },
        };

        new DataTable(table, options);
    });
});
