from django.db import migrations


def disable_modules(apps, schema_editor):
    ModuleList = apps.get_model("cms", "ModuleList")
    ModuleList.objects.filter(id__in=[5, 34]).update(status=0)


def reenable_modules(apps, schema_editor):
    ModuleList = apps.get_model("cms", "ModuleList")
    ModuleList.objects.filter(id__in=[5, 34]).update(status=1)


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0024_merge_20260820_1146"),
    ]

    operations = [
        # "Key Account Module" (id 5) and "Market Module" (id 34) are shown in
        # the sidebar as "Key Account" and "Market", but every single link
        # under both of them (KAM Actual Visit, KPDM Progress/Title/Contact/
        # Department/Program/Competitor, Market Company/Product, etc.) 404s -
        # none of the backing views/URLs were ever implemented. Hiding the
        # modules removes the dead links from the sidebar without deleting
        # the underlying menu data, in case the feature gets built later.
        migrations.RunPython(disable_modules, reenable_modules),
    ]
