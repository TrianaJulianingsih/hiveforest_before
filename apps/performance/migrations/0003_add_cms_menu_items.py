from django.db import migrations


def add_performance_menus(apps, schema_editor):
    ApplicationList = apps.get_model("cms", "ApplicationList")
    MenuItem = apps.get_model("cms", "MenuItem")

    app_id = (
        ApplicationList.objects.filter(code__icontains="HC").values_list("pk", flat=True).first()
        or ApplicationList.objects.filter(name__icontains="human").values_list("pk", flat=True).first()
        or ApplicationList.objects.order_by("pk").values_list("pk", flat=True).first()
    )
    if not app_id:
        return

    menus = [
        (
            "kpi-individual",
            "KPI Individual",
            "KPI View",
            "/performance/kpi/individual/",
            52,
            "fas fa-bullseye",
        ),
        (
            "kpi-import",
            "KPI Import",
            "Import",
            "/performance/kpi/import/",
            53,
            "fas fa-file-upload",
        ),
    ]
    for code, name, short, url, order, icon in menus:
        if MenuItem.objects.filter(code=code).exists():
            continue
        MenuItem.objects.create(
            code=code,
            name=name,
            shortname=short,
            url=url,
            application_id=app_id,
            order=order,
            icon=icon,
            status=1,
        )


def remove_performance_menus(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code__in=["kpi-individual", "kpi-import"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0002_alter_performanceobjective_unique_together"),
        ("cms", "0022_remove_applicationlist_shortname_ja"),
    ]

    operations = [
        migrations.RunPython(add_performance_menus, remove_performance_menus),
    ]
