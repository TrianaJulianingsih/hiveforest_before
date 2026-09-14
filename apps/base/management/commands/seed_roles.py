from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.base.models.permissions import CMSPermission, Role


class Command(BaseCommand):
    help = (
        "Seed a full-access Group + Role + CMSPermission (allow_all on "
        "applications/modules/menus) and attach a user to it. Re-runnable: "
        "existing rows are reused rather than duplicated."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", default="admin", help="Username to grant the role to (default: admin)."
        )
        parser.add_argument(
            "--email", default="admin@example.com", help="Email to use if the user is created."
        )
        parser.add_argument(
            "--password", default="admin123", help="Password to use if the user is created."
        )
        parser.add_argument(
            "--role-name", default="Super Admin", help="Name of the Group/Role to seed."
        )

    def handle(self, *args, **options):
        username = options["username"]
        role_name = options["role_name"]

        with transaction.atomic():
            group, _ = Group.objects.get_or_create(name=role_name)

            role, _ = Role.objects.get_or_create(
                slug=slugify(role_name),
                defaults={
                    "name": role_name,
                    "status": 1,
                    "code": slugify(role_name)[:20].upper(),
                    "shortname": role_name,
                },
            )
            role.group.add(group)

            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": options["email"], "is_staff": True, "is_superuser": True},
            )
            if created:
                user.set_password(options["password"])
                user.save()
            user.groups.add(group)
            role.user.add(user)

            CMSPermission.objects.get_or_create(
                role=role,
                apps_state="allow_all",
                mods_state="allow_all",
                menu_state="allow_all",
                status=1,
                defaults={
                    "name": f"{role_name} - Full Access",
                    "slug": slugify(f"{role_name}-full-access"),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Role '{role_name}' (group + role + allow_all permission) "
                f"seeded and granted to user '{username}'."
            )
        )
