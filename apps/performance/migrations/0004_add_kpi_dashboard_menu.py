from django.db import migrations


def add_dashboard_menu(apps, schema_editor):
    ApplicationList = apps.get_model("cms", "ApplicationList")
    MenuItem = apps.get_model("cms", "MenuItem")

    app_id = (
        ApplicationList.objects.filter(code__icontains="HC").values_list("pk", flat=True).first()
        or ApplicationList.objects.filter(name__icontains="human").values_list("pk", flat=True).first()
        or ApplicationList.objects.order_by("pk").values_list("pk", flat=True).first()
    )
    if not app_id:
        return

    code = "kpi-dashboard"
    if MenuItem.objects.filter(code=code).exists():
        return
    MenuItem.objects.create(
        code=code,
        name="KPI Dashboard",
        shortname="KPI",
        url="/performance/kpi/",
        application_id=app_id,
        order=51,
        icon="fas fa-chart-line",
        status=1,
    )


def remove_dashboard_menu(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code="kpi-dashboard").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0003_add_cms_menu_items"),
    ]

    operations = [
        migrations.RunPython(add_dashboard_menu, remove_dashboard_menu),
    ]
