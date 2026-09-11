// ╔════════════════════════════════════════════════════════════╗
// ║  Name: employe_list.js                                     ║
// ║  Type: Class Base View                                     ║
// ║  Purpose: To render datatable in list                      ║
// ╟────────────────────────────────────────────────────────────╢
// ║  Path: static\custom\js\employee_list.js                   ║
// ║  Created: ? by Setiadji                                    ║
// ║  Updated: May/23-2025 by Setiadji                          ║
// ╚════════════════════════════════════════════════════════════╝
$(document).ready(function () {
    const vis_col = JSON.parse(document.getElementById("vis-col-data").textContent);
    const totalColumns = vis_col.length; // Total number of columns
    const visibleColumns = Array.from({ length: totalColumns - 1 }, (_, i) => i + 1); // Exclude the last column (Actions)

    let table = $('#employee_table').DataTable({
        paging: true,
        searching: true,
        info: true,
        ordering: true,
        responsive: true,
        fixedHeader: true, // For large table to fixed the header on top on scrolling
        autoWidth: true,
        processing: true,
        serverSide: true,
        ajax: {
            url: '/humancapital/employee/ajax/',
            type: 'GET',
            data: function (d) {
                // Column filters
                $('.column-filter').each(function () {
                    const colIdx = $(this).data('column');
                    d['columns[' + colIdx + '][search][value]'] = $(this).val();
                });
            },
        },
        columns: [
            { data: null, orderable: false, searchable: false, render: function () {
                return '<input type="checkbox" class="action-select">';
            }},
            { data: 'id', width: '4%'},
            { data: 'code', width: '5%', type: 'string', className: 'text-start' },
            {
                data: 'name', width: '20%', 
                render: function (data, type, row) {
                    return `<a href="/humancapital/employee/${row.id}/detail/" class="text-decoration-none">${data}</a>`;
                  }
            },
            { data: 'description' },
            { data: 'gender' },
            { data: 'dob', width: '6%' },
            { data: 'national_id', type: 'string', className: 'text-start' },
            { data: 'tax_id', type: 'string', className: 'text-start' },
            { data: 'hired', width: '6%' },
            { data: 'terminated', width: '6%' },
            { data: 'remark' },
            { data: 'employment_status', width: '8%' },
            { data: 'status', width: '6%' },
            {
                data: null,
                orderable: false,
                searchable: false,
                className: 'hv-centered',
                render: function (data, type, row) {
                    const isActive = row.status == 'Active';  // Use loose equality
                    const toggleAction = isActive ? 'deactivate' : 'activate';
                    const toggleIcon = isActive ? 'fa-user-slash' : 'fa-user-check';
                    const toggleClass = isActive ? 'btn-secondary' : 'btn-success';
                    const toggleLabel = isActive ? 'Deactivate' : 'Activate';
                    const listUrl = '/humancapital/employee/';
                    const toggleUrl = `/humancapital/employee/${row.id}/change-status/?next=${encodeURIComponent(listUrl)}`;
                    const deleteUrl = `/humancapital/employee/${row.id}/soft-delete/`;

                    return `
                    <div class="btn-group">
                        <a href="/humancapital/employee/${row.id}/edit/" class="btn btn-sm btn-primary hv-btn-mini hv-action-btn">
                            <i class="far fa-edit"></i>
                        </a>
                        <div class="btn-group">
                            <button type="button" class="btn btn-sm dropdown-toggle dropdown-icon hv-btn-mini" data-toggle="dropdown" aria-expanded="true" style="border-color: blue;"></button>
                            <div class="dropdown-menu dropdown-menu-right" style="min-width: 14px !important; padding: 0.25rem;">
                                <form id="toggle-form-${row.id}" method="POST" action="${toggleUrl}" style="display:inline;">
                                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                                    <button type="button"
                                            class="btn btn-sm hv-btn-mini hv-action-btn ${toggleClass}"
                                            onclick="confirmToggleFromList(${row.id}, '${row.name.replace(/'/g, "\\'")}', '${toggleAction}')">
                                        <i class="fas ${toggleIcon} mr-1"></i>
                                    </button>
                                </form>
                                <form id="delete-form-${row.id}" method="POST" action="${deleteUrl}" style="display:inline;">
                                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                                    <button type="button" class="btn btn-sm btn-danger hv-btn-mini hv-action-btn"
                                        onclick="confirmDeleteFromList(${row.id}, '${row.name.replace(/'/g, "\\'")}')">
                                    <i class="far fa-trash-alt mr-1"></i>
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                    `;
                }
            }
        ],
        columnDefs: [
            { targets: 0, orderable: false, searchable: false, className: 'action-checkbox-column' },
            { targets: 1, orderable: true },
            { targets: 2, type: 'string' },
        ],
        buttons: [
            { extend: 'csv', className: 'btn btn-sm btn-success' },
            { extend: 'spacer', className: 'btn btn-sm btn-primary' },
            { extend: 'excel', className: 'btn btn-sm btn-success' },
            { extend: 'spacer', className: 'btn btn-sm btn-primary' },
            {
                extend: 'colvis',
                className: 'btn btn-sm btn-primary',
                text: 'Columns',
                columns: visibleColumns,
                columnText: function (dt, idx, title) {
                    // Adjust index if you skip the first column (like checkbox)
                    // Example: if vis_col[0] is for DataTables column 1
                    return vis_col[idx] || title || `Column ${idx}`;
                }
            },
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
            [5, 10, 25, 50, 100, 250, 500],
            [5, 10, 25, 50, 100, 250, 500]
        ],
        pageLength: 10,
        layout: {
            topStart: ['pageLength'],
            topEnd: ['buttons', 'search' ],
            bottomStart: ['info'],
            bottomEnd: ['paging']
        },
        initComplete: function (settings, json) {
            // Get the second row in the thead (filter inputs)
            $('#employee_table thead tr:eq(1) th')
                .removeClass('dt-orderable dt-ordering-asc dt-ordering-desc')
                .removeAttr('aria-sort') // Remove accessibility sorting info
                .find('.dt-column-order').remove(); // Remove sort arrows if injected
            $('#employee_table thead tr:eq(1) th .dt-column-title').each(function () {
                $(this).contents().unwrap(); // Keep the contents, remove the span
            });
        },
        headerCallback: function (thead, data, start, end, display) {
            const headerCheckboxCell = $(thead).find('th').eq(0);
            headerCheckboxCell.removeClass('dt-ordering-asc dt-ordering-desc');
            headerCheckboxCell.find('.dt-column-order').remove();
        }
    });

    // Filter button         
    $('#apply-filters').on('click', function () {
        table.ajax.reload();
      });

    // Reset filter button
    $('#reset-filters').on('click', function () {
        $('.filter-container input, .filter-container select, .select2-container').val('').trigger('change');
        $('.column-filter').val('');
        table.ajax.reload();
    });

    $('table.dataTable thead').on('click', 'input, select', function (e) {
        e.stopPropagation();
    });

    $('.column-filter').each(function (d) {
        const colIdx = $(this).data('column');
        d['columns[' + colIdx + '][search][value]'] = $(this).val();
    });

    // === BATCH PROCESS SECTION ===
    // Handle Field selection → populate value options
    const batchOptions = JSON.parse(document.getElementById('batch-fields-data').textContent);

    $('#batch-field').on('change', function () {
        const selectedField = $(this).val();
        const $valueSelect = $('#batch-value');
        $valueSelect.empty().append('<option value="">-- Select Value --</option>');
    
        const field = batchOptions.find(opt => opt.name === selectedField);
        if (field && field.options) {
            field.options.forEach(function (option) {
                $valueSelect.append(`<option value="${option}">${option === '__blank__' ? 'Not Stated' : option}</option>`);
            });
        }
    });    

    // Handle Go button click
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    $('#batch-go').on('click', function () {
        const field = $('#batch-field').val();
        const value = $('#batch-value').val();
        const selectedIds = [];
    
        const table = $('#employee_table').DataTable();
    
        // Correct way: Use DataTables API to get row data, not manual <td>
        $('.action-select:checked').each(function () {
            const tr = $(this).closest('tr');
            const row = table.row(tr);
    
            if (row && row.data()) {
                selectedIds.push(row.data().id);
            }
        });
    
        if (!field || !value || selectedIds.length === 0) {
            Swal.fire({
                icon: 'warning',
                title: 'Missing input',
                text: 'Please select field, value, and at least one row.',
                confirmButtonText: 'OK'
            });
            return;
        }

        $.ajax({
            url: '/humancapital/employee/batch-update/',
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            data: {
                field: field,
                value: value,
                ids: JSON.stringify(selectedIds)
            },
            success: function (res) {
                Swal.fire({
                    icon: 'success',
                    title: 'Batch update completed',
                    text: `Updated ${res.updated} records.`,
                    confirmButtonText: 'OK'
                }).then(() => {
                    table.ajax.reload();
                });
            },
            error: function (xhr) {
                Swal.fire({
                    icon: 'error',
                    title: 'Batch update failed',
                    text: xhr.responseText || 'Something went wrong.',
                    confirmButtonText: 'OK'
                });
            }
        });
    });

    // BUTTONS - Appending Buttons into the template
    table.buttons().container().appendTo('#employee_table_wrapper .col-md-6:eq(0)'); 
    $('#employee_table').DataTable().columns.adjust().draw();

    // CHECKBOX - Reapply checkbox functionality on redraw
    $('#employee_table').on('draw.dt', function () {
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
    $('#employee_table').trigger('draw.dt');

    // Update the counter on initial load
    updateCounter();

});

function confirmDeleteFromList(id, name) {
    Swal.fire({
        title: `Delete employee "${name}"?`,
        text: "This will perform a soft delete.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#aaa',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById(`delete-form-${id}`).submit();
        }
    });
}

function confirmToggleFromList(id, name, action) {
    const verb = action === 'activate' ? 'Activate' : 'Deactivate';
    const color = action === 'activate' ? '#3085d6' : '#d33'; // success or secondary

    Swal.fire({
        title: `${verb} employee "${name}"?`,
        text: `This will ${action} the employee.`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: color,
        cancelButtonColor: '#aaa',
        confirmButtonText: `Yes, ${action}`
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById(`toggle-form-${id}`).submit();
        }
    });
}