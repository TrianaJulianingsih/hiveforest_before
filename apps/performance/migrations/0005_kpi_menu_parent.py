from django.db import migrations


def restructure_kpi_menu(apps, schema_editor):
    ApplicationList = apps.get_model("cms", "ApplicationList")
    MenuItem = apps.get_model("cms", "MenuItem")

    app_id = (
        ApplicationList.objects.filter(code__icontains="HC").values_list("pk", flat=True).first()
        or ApplicationList.objects.filter(name__icontains="human").values_list("pk", flat=True).first()
        or ApplicationList.objects.order_by("pk").values_list("pk", flat=True).first()
    )
    if not app_id:
        return

    parent = MenuItem.objects.filter(code="kpi-menu").first()
    if not parent:
        parent = MenuItem.objects.create(
            code="kpi-menu",
            name="KPI",
            shortname="KPI",
            url="#",
            application_id=app_id,
            parent_id=None,
            order=48,
            icon="fas fa-chart-line",
            status=1,
        )

    child_defs = [
        ("kpi-dashboard", 1, "Home", "KPI home", "/performance/kpi/", "fas fa-home"),
        ("kpi-individual", 2, "KPI View", "KPI View", "/performance/kpi/individual/", "fas fa-bullseye"),
        ("kpi-import", 3, "Import", "Import", "/performance/kpi/import/", "fas fa-file-upload"),
    ]
    for code, order, shortname, name, url, icon in child_defs:
        m = MenuItem.objects.filter(code=code).first()
        if m:
            m.parent_id = parent.pk
            m.order = order
            m.shortname = shortname[:25]
            m.name = name[:100]
            m.url = url
            m.icon = icon
            m.application_id = app_id
            m.save()
        else:
            MenuItem.objects.create(
                code=code,
                name=name[:100],
                shortname=shortname[:25],
                url=url,
                application_id=app_id,
                parent_id=parent.pk,
                order=order,
                icon=icon,
                status=1,
            )


def undo_kpi_menu_parent(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    for code in ("kpi-dashboard", "kpi-individual", "kpi-import"):
        m = MenuItem.objects.filter(code=code).first()
        if m:
            m.parent_id = None
            m.save()
    MenuItem.objects.filter(code="kpi-menu").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0004_add_kpi_dashboard_menu"),
    ]

    operations = [
        migrations.RunPython(restructure_kpi_menu, undo_kpi_menu_parent),
    ]
