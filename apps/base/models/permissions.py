from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Group
from apps.base.models.abstracts import GenericAbstract
from apps.base.choices import PermissionState

class SCMPermission(GenericAbstract):
    code = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    role = models.ForeignKey('base.Role', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Role")
    distributor_state = models.CharField(max_length=10, choices=PermissionState.choices, default=PermissionState.NOT_SET, verbose_name="Distributor State")
    distributor = models.ManyToManyField('supplychain.Distributor', blank=True, verbose_name="Distributor")
    branch_state = models.CharField(max_length=10, choices=PermissionState.choices, default=PermissionState.NOT_SET, verbose_name="Branch State")
    branch = models.ManyToManyField('supplychain.Branch', blank=True, verbose_name="Branch")
    distitemgroup_state = models.CharField(max_length=10, choices=PermissionState.choices, default=PermissionState.NOT_SET, verbose_name="Dist. Item Group State")
    distitemgroup = models.ManyToManyField('supplychain.DistributorItemGroup', blank=True, verbose_name="Dist. Item Group")
    mfgitemgroup_state = models.CharField(max_length=10, choices=PermissionState.choices, default=PermissionState.NOT_SET, verbose_name="Mfg. Item Group State")
    mfgitemgroup = models.ManyToManyField('supplychain.ManufacturingItemGroup', blank=True, verbose_name="Mfg. Item Group")

    def __str__(self):
        return f"Role: {self.role}, Dist.: {self.distributor_state}, Branch: {self.branch_state}, Dist. Item Group: {self.distitemgroup_state}, Mfg. Item Group: {self.mfgitemgroup_state}"

    class Meta:
        verbose_name = "SCM Permission"
        verbose_name_plural = "SCM Permissions"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
        unique_together = (
            'role',
            'distributor_state',
            'branch_state',
            'distitemgroup_state',
            'mfgitemgroup_state',
            'status',
        )

    @staticmethod
    def has_permission(user, distributor=None, branch=None, distitemgroup=None, mfgitemgroup=None,):
        # Get user roles
        groups = Group.objects.filter(user=user)
        roles = Role.objects.filter(user=user) | Role.objects.filter(group__in=groups)

        if not roles.exists():
            return False

        query = Q(role__in=roles) # Base query for user roles
        if distributor:
            query &= Q(
                Q(distributor_state='allow_all') |
                Q(distributor_state='allow', distributor=distributor)
            ) & ~Q(distributor_state='deny', distributor=distributor)
            # If deny_all is set, deny all access
            if SCMPermission.objects.filter(role__in=roles, distributor_state='deny_all').exists():
                return False

        if branch:
            query &= Q(
                Q(branch_state='allow_all') |
                Q(branch_state='allow', branch=branch)
            ) & ~Q(branch_state='deny', branch=branch)

            # If deny_all is set, deny all access
            if SCMPermission.objects.filter(role__in=roles, branch_state='deny_all').exists():
                return False

        if distitemgroup:
            query &= Q(
                Q(distitemgroup_state='allow_all') |
                Q(distitemgroup_state='allow', distpg=distitemgroup)
            ) & ~Q(distitemgroup_state='deny', distpg=distitemgroup)

            # If deny_all is set, deny all access
            if SCMPermission.objects.filter(role__in=roles, distitemgroup_state='deny_all').exists():
                return False

        if mfgitemgroup:
            query &= Q(
                Q(mfgitemgroup_state='allow_all') |
                Q(mfgitemgroup_state='allow', mfgpg=mfgitemgroup)
            ) & ~Q(mfgitemgroup_state='deny', mfgpg=mfgitemgroup)

            # If deny_all is set, deny all access
            if SCMPermission.objects.filter(role__in=roles, mfgitemgroup_state='deny_all').exists():
                return False

        # Check if the query matches any RolePermission
        return SCMPermission.objects.filter(query).exists()

class CMSPermission(GenericAbstract):
    code = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    role = models.ForeignKey('base.Role', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Role")
    apps_state = models.CharField(max_length=10, choices=PermissionState.choices, default=PermissionState.NOT_SET, verbose_name="Application State")
    application = models.ManyToManyField('cms.ApplicationList', blank=True, verbose_name="Application")
    mods_state = models.CharField(max_length=10, choices=PermissionState.choices, default=PermissionState.NOT_SET, verbose_name="Module State")
    module = models.ManyToManyField('cms.ModuleList', blank=True, verbose_name="Module")
    menu_state = models.CharField(max_length=10, choices=PermissionState.choices, default=PermissionState.NOT_SET, verbose_name="Menu State")
    menu = models.ManyToManyField('cms.MenuItem', blank=True, verbose_name="Menu")

    def __str__(self):
        return f"Role: {self.role}, Applications: {self.apps_state}, Modules: {self.mods_state}, Menus: {self.menu_state}"

    class Meta:
        verbose_name = "CMS Permission"
        verbose_name_plural = "CMS Permissions"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

        unique_together = (
            'role',
            'apps_state',
            'mods_state',
            'menu_state',
            'status',
        )

    @staticmethod
    def has_permission(user, application=None, module=None, menu=None):
        # Get user roles
        groups = Group.objects.filter(user=user)
        roles = Role.objects.filter(user=user) | Role.objects.filter(group__in=groups)

        if not roles.exists():
            return False

        query = Q(role__in=roles) # Base query for user roles
        if application:
            query &= Q(
                Q(apps_state='allow_all') |
                Q(apps_state='allow', application=application)
            ) & ~Q(apps_state='deny', application=application)
            # If deny_all is set, deny all access
            if CMSPermission.objects.filter(role__in=roles, apps_state='deny_all').exists():
                return False

        if module:
            query &= Q(
                Q(mods_state='allow_all') |
                Q(mods_state='allow', module=module)
            ) & ~Q(mods_state='deny', module=module)

            # If deny_all is set, deny all access
            if CMSPermission.objects.filter(role__in=roles, mods_state='deny_all').exists():
                return False

        # Menu permission check
        if menu:
            query &= Q(
                Q(menu_state='allow_all') |
                Q(menu_state='allow', menu=menu)
            ) & ~Q(menu_state='deny', menu=menu)

            # If deny_all is set, deny all access
            if CMSPermission.objects.filter(role__in=roles, menu_state='deny_all').exists():
                return False

        # Check if the query matches any RolePermission
        return CMSPermission.objects.filter(query).exists()
             
class Role(GenericAbstract):
    code = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Code")
    initial = models.CharField(max_length=12, null=True, blank=True, default="", verbose_name="Initial")
    shortname = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="Shortname")
    user = models.ManyToManyField(User, related_name='role', blank=True)
    group = models.ManyToManyField(Group, related_name='role', blank=True)

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        ordering = ("name",)
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]

    def __str__(self):
        return self.name