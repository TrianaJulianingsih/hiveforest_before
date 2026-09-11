import re
from pathlib import Path

org = Path("static/custom/js/organization_list.js").read_text(encoding="utf-8")


def make_list(prefix, table_id, entity_label, columns_block):
    s = org
    s = s.replace("organization_list.js", f"{prefix}_list.js")
    s = s.replace("buildOrganizationUrl", f"build{prefix.title().replace('_', '')}Url")
    s = s.replace("organizationBaseUrl", f"{prefix}BaseUrl")
    s = s.replace("#organization_table", f"#{table_id}")
    s = s.replace("organization", prefix)
    s = s.replace("Organization", entity_label)
    s = s.replace("/detail/", "/edit/")
    s = re.sub(
        r"        columns: \[.*?\n        \],\n        columnDefs:",
        "        columns: [\n" + columns_block + "\n        ],\n        columnDefs:",
        s,
        count=1,
        flags=re.DOTALL,
    )
    # Fix function name casing: buildPerformancemodelUrl -> buildPerformanceModelUrl
    camel = "".join(part.capitalize() for part in prefix.split("_"))
    s = s.replace(f"build{camel}Url", f"build{camel}Url")
    if prefix == "performancemodel":
        s = s.replace("buildPerformancemodelUrl", "buildPerformanceModelUrl")
    if prefix == "performancegroup":
        s = s.replace("buildPerformancegroupUrl", "buildPerformanceGroupUrl")
    Path(f"static/custom/js/{prefix}_list.js").write_text(s, encoding="utf-8")
    print("wrote", prefix)


model_cols = """
            { data: null, orderable: false, searchable: false, render: function () {
                return '<input type="checkbox" class="action-select">';
            }},
            { data: 'id' },
            { data: 'code', type: 'string', className: 'text-start' },
            {
                data: 'name',
                render: function (data, type, row) {
                    return `<a href="${buildPerformanceModelUrl(`${row.id}/edit/`)}" class="text-decoration-none">${data || ''}</a>`;
                }
            },
            { data: 'initial' },
            { data: 'shortname' },
            { data: 'description' },
            { data: 'status' },"""

group_cols = """
            { data: null, orderable: false, searchable: false, render: function () {
                return '<input type="checkbox" class="action-select">';
            }},
            { data: 'id' },
            { data: 'code', type: 'string', className: 'text-start' },
            {
                data: 'name',
                render: function (data, type, row) {
                    return `<a href="${buildPerformanceGroupUrl(`${row.id}/edit/`)}" class="text-decoration-none">${data || ''}</a>`;
                }
            },
            { data: 'description' },
            { data: 'bobot' },
            { data: 'performance_model__code' },
            { data: 'sort_order' },
            { data: 'initial' },
            { data: 'shortname' },
            { data: 'status' },"""

make_list("performancemodel", "performancemodel_table", "Performance Model", model_cols)
make_list("performancegroup", "performancegroup_table", "Performance Group", group_cols)
