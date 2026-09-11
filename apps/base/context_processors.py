from apps.base.models.permissions import Role, CMSPermission
from apps.cms.models.appmanagers import ApplicationList
from apps.cms.models.modmanagers import ModuleList
from apps.cms.models.menusystem import MenuItem
from django.contrib.auth.models import Group
from collections import defaultdict
from django.urls import resolve
from django.utils.text import capfirst
from urllib.parse import unquote, urlparse, parse_qs
from django.conf import settings
from apps.base.models.version import AppVersion


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: has_access                                          ║
# ║  Type: Function Based View                                 ║
# ║  Purpose: To handle menu access                            ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\context_processors.py                     ║
# ║  Created:                                                  ║
# ║  Updated: Jun/3-2025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
def _resolve_allowed_ids(roles, state_prefix, m2m_field):
    """Bulk-resolve which target ids (application/module/menu) the given roles
    grant access to for one permission dimension, replicating what
    CMSPermission.has_permission() decides per item - but in a fixed handful
    of queries instead of one has_permission() call (~4-5 queries each) per
    candidate row. With ~110 active apps+modules+menus, the old per-item loop
    meant 400-500+ round trips to the (remote) database on every single page
    render, which was the actual source of multi-second page loads app-wide.
    Returns None as a sentinel meaning "every active item is allowed" (an
    allow_all permission was found), or a set of specifically-allowed ids.
    """
    state_field = f"{state_prefix}_state"
    if CMSPermission.objects.filter(role__in=roles, **{state_field: "deny_all"}).exists():
        return set()
    if CMSPermission.objects.filter(role__in=roles, **{state_field: "allow_all"}).exists():
        return None
    return set(
        CMSPermission.objects.filter(role__in=roles, **{state_field: "allow"}).values_list(
            m2m_field, flat=True
        )
    )


def has_access(request):
    if not request.user.is_authenticated:
        return {"apps_access": [], "mods_access": {}, "menu_access": {}}
    user = request.user
    groups = Group.objects.filter(user=user)
    roles = Role.objects.filter(user=user) | Role.objects.filter(group__in=groups)

    # Application permissions
    allowed_app_ids = _resolve_allowed_ids(roles, "apps", "application")
    apps_access = ApplicationList.objects.filter(status=1)
    if allowed_app_ids is not None:
        apps_access = apps_access.filter(id__in=allowed_app_ids)
    apps_access = apps_access.order_by("order").distinct()

    # Module permissions
    allowed_mod_ids = _resolve_allowed_ids(roles, "mods", "module")
    modules = ModuleList.objects.filter(status=1)
    if allowed_mod_ids is not None:
        modules = modules.filter(id__in=allowed_mod_ids)
    modules = modules.order_by("order").distinct()

    # Map modules to applications
    mods_access = defaultdict(list)
    for module in modules:
        mods_access[module.application_id].append(module)

    # Menus permissions
    allowed_menu_ids = _resolve_allowed_ids(roles, "menu", "menu")
    menus = MenuItem.objects.filter(status=1)
    if allowed_menu_ids is not None:
        menus = menus.filter(id__in=allowed_menu_ids)
    menus = menus.order_by("order").distinct()
    # Map menus to modules
    menu_access = defaultdict(list)
    menu_by_module = defaultdict(list)
    for menu in menus:
        menu_by_module[menu.module_id].append(menu)

    for module_id, menu_list in menu_by_module.items():
        menu_access[module_id] = build_menu_tree(menu_list)

    menu_by_application = defaultdict(list)
    for menu in menus:
        if menu.module_id is None and menu.parent_id is None and menu.application_id:
            menu_by_application[menu.application_id].append(menu)

    for app_id, menu_list in menu_by_application.items():
        menu_access[f"app_{app_id}"] = build_menu_tree(menu_list)

    return {
        "apps_access": apps_access,
        "mods_access": dict(mods_access),
        "menu_access": dict(menu_access),
    }


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_menu_tree                                     ║
# ║  Type: Function Based View                                 ║
# ║  Purpose: To handle menu tree                              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\context_processors.py                     ║
# ║  Created:                                                  ║
# ║  Updated:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
def build_menu_tree(flat_menus):
    menu_dict = {menu.id: menu for menu in flat_menus}
    for menu in flat_menus:
        menu.children_list = []

    root_menus = []
    for menu in flat_menus:
        if menu.parent_id:
            parent = menu_dict.get(menu.parent_id)
            if parent:
                parent.children_list.append(menu)
        else:
            root_menus.append(menu)

    return root_menus


def breadcrumbs(request):
    path = request.path.strip("/")  # Remove leading/trailing slashes
    segments = path.split("/")  # Split URL path into segments
    query_params = parse_qs(request.GET.urlencode())  # Parse query parameters

    breadcrumbs = []
    url = ""

    # Build breadcrumbs for hierarchical structure
    for segment in segments:
        if segment.isdigit():  # Handle IDs (e.g., /product/42/)
            continue  # Skip adding raw IDs in breadcrumbs
        url += f"/{segment}"
        name = unquote(segment.replace("-", " "))  # Replace '-' with space
        breadcrumbs.append({"name": capfirst(name), "url": url})

    # Handle special cases for detail pages with IDs
    if segments[-1].isdigit():
        breadcrumbs.append({"name": f"ID {segments[-1]}", "url": request.path})

    # Handle query parameters (non-hierarchical)
    if query_params:
        query_str = "&".join(f"{k}={v[0]}" for k, v in query_params.items())
        breadcrumbs.append(
            {"name": f"Search: {query_str}", "url": f"{request.path}?{query_str}"}
        )

    return {"breadcrumbs": breadcrumbs}


def project_settings(request):
    return {"PROJECT_NAME": settings.PROJECT_NAME}


# ═══════════════════════════════════════════════════════════
# FaisalS | Version History App
# ═══════════════════════════════════════════════════════════
def version_context(request):
    current_version = AppVersion.get_current_version()
    return {
        "app_version": (
            f"{current_version.version_number}-{current_version.title}"
            if current_version
            else None
        ),
        "app_version_full": current_version if current_version else None,
        "version": current_version,
    }
