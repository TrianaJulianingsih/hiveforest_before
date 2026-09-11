from django.db import migrations


def update_kpi_submenus(apps, schema_editor):
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

    child_defs = [
        ("kpi-dashboard", 1, "Home", "KPI home", "/performance/kpi/", "fas fa-home"),
        ("kpi-individual", 2, "KPI View", "KPI View", "/performance/kpi/individual/", "fas fa-bullseye"),
        ("kpi-manual", 3, "Manual", "Manual entry", "/performance/kpi/period/new/", "fas fa-edit"),
        ("kpi-periods", 4, "Periods", "All periods", "/performance/kpi/periods/", "fas fa-table"),
        ("kpi-import", 5, "Import", "Import", "/performance/kpi/import/", "fas fa-file-upload"),
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


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0005_kpi_menu_parent"),
    ]

    operations = [
        migrations.RunPython(update_kpi_submenus, noop_reverse),
    ]
