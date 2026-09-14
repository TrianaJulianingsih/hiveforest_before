from django.db import migrations

# The original PowerBI iframe dashboards (CR100 "Hospital Profile" and CR200
# "Doctor Profile") stay exactly as they were. These are NEW sidebar entries
# that sit alongside them and land directly on the profile-card page (built
# this session from the imported hospital-profile-html / doctor-profile-html
# designs) for a representative record, since a "dashboard" menu item has no
# single hospital/doctor pk to key off of.
NEW_MENU_ITEMS = [
    {
        "code": "CR101",
        "initial": "HSPDashV2",
        "name": "Hospital Profile Dashboard",
        "shortname": "Hospital Dashboard",
        "slug": "hospital-profile-dashboard-page",
        "icon": "fas fa-hospital menu-icon",
        "url": "/crm/dashboard/hospital/profile/",
        "order": 1,
        "application_code": "CR100",
        "module_code": "CR100",
    },
    {
        "code": "CR203",
        "initial": "DocDashV2",
        "name": "Doctor Profile Dashboard",
        "shortname": "Doctor Dashboard",
        "slug": "doctor-profile-dashboard-page",
        "icon": "fas fa-user-md menu-icon",
        "url": "/crm/dashboard/hcp/profile/",
        "order": 1,
        "application_code": "CR200",
        "module_code": "CR200",
    },
]


def add_menu_items(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    reference = {
        "CR100": MenuItem.objects.get(code="CR100"),
        "CR200": MenuItem.objects.get(code="CR200"),
    }

    for item in NEW_MENU_ITEMS:
        ref = reference[item["application_code"]]
        MenuItem.objects.get_or_create(
            code=item["code"],
            defaults={
                "initial": item["initial"],
                "name": item["name"],
                "shortname": item["shortname"],
                "slug": item["slug"],
                "icon": item["icon"],
                "url": item["url"],
                "order": item["order"],
                "parent": None,
                "application": ref.application,
                "module": ref.module,
                "status": ref.status,
                "cby": ref.cby,
            },
        )


def remove_menu_items(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code__in=["CR101", "CR203"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0032_seed_hcp_translations_and_menu_labels"),
        ("cms", "0023_alter_menuitem_iframe_url"),
    ]

    operations = [
        migrations.RunPython(add_menu_items, remove_menu_items),
    ]
