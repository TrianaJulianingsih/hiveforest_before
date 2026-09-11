from django.db import migrations


def add_group_menu(apps, schema_editor):
    ApplicationList = apps.get_model("cms", "ApplicationList")
    MenuItem = apps.get_model("cms", "MenuItem")

    app_id = (
        ApplicationList.objects.filter(code__icontains="HC").values_list("pk", flat=True).first()
        or ApplicationList.objects.filter(name__icontains="human").values_list("pk", flat=True).first()
        or ApplicationList.objects.order_by("pk").values_list("pk", flat=True).first()
    )
    parent = MenuItem.objects.filter(code="kpi-menu").first()
    if not app_id or not parent:
        return

    MenuItem.objects.get_or_create(
        code="kpi-groups",
        defaults={
            "name": "Performance Groups",
            "application_id": app_id,
            "parent": parent,
            "url": "/performance/kpi/groups/",
            "icon": "fas fa-layer-group",
            "order": 6,
            "status": 1,
            "deleted": False,
        },
    )


def remove_group_menu(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code="kpi-groups").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0007_performancegroup_bobot"),
        ("cms", "0022_remove_applicationlist_shortname_ja"),
    ]

    operations = [
        migrations.RunPython(add_group_menu, remove_group_menu),
    ]
