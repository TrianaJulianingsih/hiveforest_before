from django.db import migrations


def add_models_menu(apps, schema_editor):
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
        code="kpi-models",
        defaults={
            "name": "Performance Models",
            "application_id": app_id,
            "parent": parent,
            "url": "/performance/kpi/models/",
            "icon": "fas fa-tags",
            "order": 5,
            "status": 1,
            "deleted": False,
        },
    )


def remove_models_menu(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code="kpi-models").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0008_add_group_management_menu"),
        ("cms", "0022_remove_applicationlist_shortname_ja"),
    ]

    operations = [
        migrations.RunPython(add_models_menu, remove_models_menu),
    ]
