from django.db import migrations

# CR203 ("Doctor Profile Dashboard") redirected to a single (first) doctor's
# profile. It's redundant now that CR201 ("Healthcare Professionals" /
# shortname "Doctor List") already links to the full, searchable doctor list
# at /crm/dashboard/hcp/, from which any doctor's profile is reachable.
REMOVED_ITEM = {
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
}


def remove_menu_item(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code="CR203").delete()


def restore_menu_item(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    reference = MenuItem.objects.get(code=REMOVED_ITEM["application_code"])
    MenuItem.objects.get_or_create(
        code=REMOVED_ITEM["code"],
        defaults={
            "initial": REMOVED_ITEM["initial"],
            "name": REMOVED_ITEM["name"],
            "shortname": REMOVED_ITEM["shortname"],
            "slug": REMOVED_ITEM["slug"],
            "icon": REMOVED_ITEM["icon"],
            "url": REMOVED_ITEM["url"],
            "order": REMOVED_ITEM["order"],
            "parent": None,
            "application": reference.application,
            "module": reference.module,
            "status": reference.status,
            "cby": reference.cby,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0034_hospital_list_menu_item"),
    ]

    operations = [
        migrations.RunPython(remove_menu_item, restore_menu_item),
    ]
