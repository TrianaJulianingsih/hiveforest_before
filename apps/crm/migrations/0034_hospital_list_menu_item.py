from django.db import migrations

OLD_VALUES = {
    "name": "Hospital Profile Dashboard",
    "shortname": "Hospital Dashboard",
    "url": "/crm/dashboard/hospital/profile/",
}

NEW_VALUES = {
    "name": "Hospital List",
    "shortname": "Hospital List",
    "url": "/crm/dashboard/hospital/",
}


def point_to_hospital_list(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code="CR101").update(**NEW_VALUES)


def revert_to_profile_dashboard(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code="CR101").update(**OLD_VALUES)


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0033_add_profile_dashboard_menu_items"),
    ]

    operations = [
        migrations.RunPython(point_to_hospital_list, revert_to_profile_dashboard),
    ]
