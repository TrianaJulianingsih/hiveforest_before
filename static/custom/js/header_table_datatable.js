$(document).ready(function () {
    let table = $('#header_table').DataTable({
        paging: true,
        searching: true,
        info: true,
        ordering: true,
        responsive: true,
        fixedHeader: true, // For large table to fixed the header on top on scrolling
        autoWidth: false,
        columns: [
            {
                data: null,
                render: function (data, type, row) {
                    return '<input type="checkbox" name="_selected_action" value="' + row.id + '" class="action-select" aria-label="Select this object for an action">';}
                },
            { data: 'IDs' },
            { data: 'Order No' },
            { data: 'Distributor' },
            { data: 'Branch' },
            { data: 'Type' },
            { data: 'Date' },
            { data: 'Due' },
            { data: 'Description' },
            { data: 'Remark' },
            { data: 'Lines' },
            { data: 'Value' },
            { data: 'Progress' },
            { data: 'Status' },
            { data: 'Created At' },
            { data: 'Created By' },
            { data: 'Action' },
        ],
        columnDefs: [
            { targets: 0, orderable: false, searchable: false, className: 'action-checkbox-column' },
            { targets: 2, type: 'string' },
            { targets: 16, orderable: false },
        ],
        buttons: [
            { extend: 'csv', className: 'btn btn-sm btn-success' },
            { extend: 'excel', className: 'btn btn-sm btn-success' },
            { extend: 'pdf', className: 'btn btn-sm btn-success' },
            { extend: 'spacer', className: 'btn btn-sm btn-primary' },
            { extend: 'print', className: 'btn btn-sm btn-warning' },
            { extend: 'copy', className: 'btn btn-sm btn-warning' },
            { extend: 'spacer', className: 'btn btn-sm btn-warning' },
            { extend: 'colvis', className: 'btn btn-sm btn-primary', text: 'Columns', columns: ':visible' }
        ],
        language: {
            paginate: {
                first: "First",
                last: "Last",
                previous: "Previous",
                next: "Next"
            },
            buttons: {
                colvis: 'Columns'
            },
            lengthMenu: "Show _MENU_ entries"
        },
        lengthMenu: [
            [5, 10, 25, 50, 100, 250, 500, -1],
            [5, 10, 25, 50, 100, 250, 500, "All"]
        ],
        pageLength: 10,
        layout: {
            topStart: ['pageLength'],
            topEnd: ['buttons', 'search' ],
            bottomStart: ['info'],
            bottomEnd: ['paging']
        },
        headerCallback: function (thead, data, start, end, display) {
            const headerCheckboxCell = $(thead).find('th').eq(0);
            headerCheckboxCell.removeClass('dt-ordering-asc dt-ordering-desc');
            headerCheckboxCell.find('.dt-column-order').remove();
        }
    });

    // BUTTONS - Appending Buttons into the template
    table.buttons().container().appendTo('#header_table_wrapper .col-md-6:eq(0)'); 
    $('#header_table').DataTable().columns.adjust().draw();

    // CHECKBOX - Reapply checkbox functionality on redraw
    $('#header_table').on('draw.dt', function () {
        // Rebind the header checkbox click event
        $('#action-toggle').off('click').on('click', function() {
            const checked = this.checked; // Check/uncheck state
            $('.action-select').prop('checked', this.checked); // Update all row checkboxes
        });
        // Rebind row checkbox click events (optional: toggle header checkbox based on all rows)
        $('.action-select').off('click').on('click', function () {
            const allChecked = $('.action-select').length === $('.action-select:checked').length;
            $('#action-toggle').prop('checked', allChecked); // Update header checkbox state
        });
    });

    // Update Counter Function
    function updateCounter() {
        const selectedCount = document.querySelectorAll('.action-select:checked').length;
        const totalCount = `${table.rows().count()}`;
        document.querySelectorAll('.action-counter').forEach(counter => {
            counter.textContent = `${selectedCount} of ${totalCount} selected`;
        });
    }
    
    // Checkboxes & counter reset on page change
    table.on('draw.dt', function () {
        const selectedCount = 0;
        const totalCount = `${table.rows().count()}`;
        document.querySelectorAll('.action-select').forEach(checkbox => {
            checkbox.checked = false;
        });
        const actionToggle = document.getElementById('action-toggle');
        if (actionToggle) {
            actionToggle.checked = false;
        }
        document.querySelectorAll('.action-counter').forEach(counter => {
            counter.textContent = `${selectedCount} of ${totalCount} selected`;
        });
    });
    
    // Listen to individual checkbox changes
    document.addEventListener('change', function (event) {
        if (event.target.classList.contains('action-select')) {
            updateCounter();
        }
    });
    
    // Listen to "select all" toggle
    const actionToggle = document.getElementById('action-toggle');
    if (actionToggle) {
        actionToggle.addEventListener('click', function () {
            const allChecked = this.checked;
            document.querySelectorAll('.action-select').forEach(checkbox => {
                checkbox.checked = allChecked;
            });
            updateCounter();
        });
    }
    
    // Update counter on initial load
    updateCounter();

    // Update counter on page length change
    table.on('length.dt', function () {
        updateCounter();
    });
    
    // PAGELENGTH - Change page length dynamically
    table.page.len(10).draw(); // Sets page length to 5 and redraws the table
    
    // Listen for the server-side search form submission
    const searchForm = document.querySelector('.search-container form');
    if (searchForm) {
        searchForm.addEventListener('submit', function () {
            setTimeout(function () {
                // Reset DataTables pagination and redraw
                table.page.len(10).draw(false); // Adjust page length as needed
            }, 100); // Delay to allow the server to respond and reload data
        });
    }
    
    // Trigger the draw event manually on initial load to bind events
    $('#header_table').trigger('draw.dt');

    // Update the counter on initial load
    updateCounter();

});      