from django.db import migrations


MENU_CODE = "CMS-MENU-SM-TA"
MENU_URL = "/sales/territory/territory-assignment"
MENU_NAME = "Territory Assignment"
MENU_SHORTNAME = "Territory Assignment"
MENU_ICON = "nav-icon fas fa-circle"
MODULE_NAME = "Territory Management Module"
MODULE_SHORTNAME = "Territory Management"
APPLICATION_NAME = "Sales Management"
APPLICATION_SHORTNAME = "Sales"


def seed_territory_assignment_menu(apps, schema_editor):
    ApplicationList = apps.get_model("cms", "ApplicationList")
    ModuleList = apps.get_model("cms", "ModuleList")
    MenuItem = apps.get_model("cms", "MenuItem")

    application = (
        ApplicationList.objects.filter(name=APPLICATION_NAME).first()
        or ApplicationList.objects.filter(shortname=APPLICATION_SHORTNAME).first()
    )
    if application is None:
        return

    module = (
        ModuleList.objects.filter(application=application, name=MODULE_NAME).first()
        or ModuleList.objects.filter(application=application, shortname=MODULE_SHORTNAME).first()
    )
    if module is None:
        return

    menu = MenuItem.objects.filter(code=MENU_CODE).first()
    if menu is None:
        menu = MenuItem.objects.filter(url=MENU_URL, module=module).first()

    if menu is None:
        menu = MenuItem(code=MENU_CODE)

    menu.name = MENU_NAME
    menu.shortname = MENU_SHORTNAME
    menu.initial = "TA"
    menu.application = application
    menu.module = module
    menu.icon = MENU_ICON
    menu.url = MENU_URL
    menu.order = 2
    menu.status = 1
    menu.deleted = False
    menu.save()


def remove_territory_assignment_menu(apps, schema_editor):
    MenuItem = apps.get_model("cms", "MenuItem")
    MenuItem.objects.filter(code=MENU_CODE, url=MENU_URL).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0022_remove_applicationlist_shortname_ja"),
    ]

    operations = [
        migrations.RunPython(seed_territory_assignment_menu, remove_territory_assignment_menu),
    ]
