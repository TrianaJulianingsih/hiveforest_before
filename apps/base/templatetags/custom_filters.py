from django import template
from django.urls import resolve, Resolver404
from django.conf import settings

register = template.Library()


def _path_contains_segment(path: str, pattern: str) -> bool:
    if not path or not pattern:
        return False
    segment = f"/{pattern}"
    index = path.find(segment)
    if index == -1:
        return False
    end_index = index + len(segment)
    if end_index == len(path):
        return True
    next_char = path[end_index]
    return next_char in {"/", "?", "#"}


@register.simple_tag(takes_context=True)
def active_admin(context, *patterns):
    request = context.get("request")
    if not request:
        return ""

    for pattern in patterns:
        if not pattern:
            continue

        if _path_contains_segment(request.path, pattern):
            return "active"

        try:
            match = resolve(request.path)
        except Resolver404:
            match = None

        if match and match.url_name == pattern:
            return "active"

    return ""


@register.simple_tag(takes_context=True)
def menu_open_admin(context, *patterns):
    request = context.get("request")
    if not request:
        return ""

    for pattern in patterns:
        if not pattern:
            continue

        if pattern in request.path:
            return "menu-open"

        try:
            if resolve(request.path).url_name == pattern:
                return "menu-open"
        except Resolver404:
            pass

        if "/" in pattern:
            app, model = pattern.split("/", 1)
            if f"/{app}/{model}" in request.path:
                return "menu-open"

    return ""


@register.filter(name="dict_key")
def dict_key(dictionary, key):
    if not isinstance(dictionary, dict):
        return []
    return dictionary.get(key, [])


@register.filter(name="dotformat")
def dotformat(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    return f"{value:,}".replace(",", ".")


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    request = context.get("request")
    if not request:
        return ""
    if pattern_or_urlname and pattern_or_urlname in request.path:
        return "active"
    try:
        if resolve(request.path).url_name == pattern_or_urlname:
            return "active"
    except Resolver404:
        pass
    return ""


@register.simple_tag(takes_context=True)
def menu_open(context, *patterns):
    request = context.get("request")
    if not request:
        return ""
    for pattern in patterns:
        if not pattern:
            continue
        if pattern in request.path:
            return "menu-open"
        try:
            if resolve(request.path).url_name == pattern:
                return "menu-open"
        except Resolver404:
            pass
    return ""


def _normalized_path(path: str) -> str:
    if not path:
        return ""
    path = path.split("?")[0].split("#")[0]
    codes = {code for code, _ in getattr(settings, "LANGUAGES", [])}
    segments = path.lstrip("/").split("/")
    if segments and segments[0] in codes:
        segments = segments[1:]
        path = "/" + "/".join(segments)
        if path == "/":
            path = "/"
    if path.endswith("/") and path != "/":
        path = path[:-1]
    return path or "/"


def _segment_prefix_match(current_norm: str, candidate_norm: str) -> bool:
    if not candidate_norm:
        return False
    base = candidate_norm.rstrip("/")
    if current_norm == base:
        return True
    if current_norm.startswith(base):
        idx = len(base)
        if len(current_norm) == idx or current_norm[idx] == "/":
            return True
    return False


def _normalized_pattern(pattern: str, *, force_admin: bool = False) -> str:
    if not pattern:
        return ""
    pattern = pattern.strip()
    if not pattern:
        return ""
    if not pattern.startswith("/"):
        pattern = f"/{pattern}"
    if force_admin and not pattern.startswith("/admin/"):
        pattern = f"/admin{pattern}"
    return _normalized_path(pattern)


@register.simple_tag(takes_context=True)
def safe_menu_active(context, menu_url):
    request = context.get("request")
    if not request or not menu_url:
        return ""
    current = _normalized_path(request.path)
    raw_target = str(menu_url)
    target = _normalized_path(raw_target)
    force_admin = current.startswith("/admin/")
    if force_admin and not target.startswith("/admin/") and not raw_target.startswith("http"):
        target = _normalized_pattern(raw_target, force_admin=True)
    if target in {"", "#"}:
        return ""
    if _segment_prefix_match(current, target):
        return "active"
    return ""


@register.simple_tag(takes_context=True)
def safe_menu_open(context, menu_url):
    request = context.get("request")
    if not request or not menu_url:
        return ""
    current = _normalized_path(request.path)
    raw_target = str(menu_url)
    target = _normalized_path(raw_target)
    force_admin = current.startswith("/admin/")
    if force_admin and not target.startswith("/admin/") and not raw_target.startswith("http"):
        target = _normalized_pattern(raw_target, force_admin=True)
    if target in {"", "#"}:
        return ""
    if _segment_prefix_match(current, target):
        return "menu-open"
    return ""


def _iter_descendant_urls(menu, depth=0, max_depth=10):
    if depth > max_depth or menu is None:
        return
    children_candidates = []
    if isinstance(menu, dict):
        for key in ("children_list", "children", "items"):
            value = menu.get(key)
            if value:
                try:
                    children_candidates = list(value)
                except Exception:
                    children_candidates = []
                break
    else:
        for attr in ("children_list", "children", "items"):
            if hasattr(menu, attr):
                value = getattr(menu, attr)
                if value:
                    try:
                        children_candidates = list(value)
                    except Exception:
                        children_candidates = []
                    break
    for child in children_candidates:
        url = (
            child.get("url") if isinstance(child, dict) else getattr(child, "url", None)
        )
        if url and url not in ("", "#"):
            yield str(url)
        yield from _iter_descendant_urls(child, depth + 1, max_depth=max_depth)


def _collect_all_urls(menu):
    urls = []
    base_url = menu.get("url") if isinstance(menu, dict) else getattr(menu, "url", None)
    if base_url:
        urls.append(str(base_url))
    for u in _iter_descendant_urls(menu):
        urls.append(u)
    return urls


def _matches_path(current_norm, candidate_norm):
    if not candidate_norm or candidate_norm in {"", "#"}:
        return False
    return _segment_prefix_match(current_norm, candidate_norm)


@register.simple_tag(takes_context=True)
def menu_group_open(context, *groups):
    request = context.get("request")
    if not request:
        return ""
    current = _normalized_path(request.path)
    for group in groups:
        if not group:
            continue
        try:
            iterable = list(group)
        except Exception:
            iterable = []
        for menu in iterable:
            for url in _collect_all_urls(menu):
                if _matches_path(current, _normalized_path(url)):
                    return "menu-open"
    return ""


@register.simple_tag(takes_context=True)
def menu_group_active(context, *groups):
    request = context.get("request")
    if not request:
        return ""
    current = _normalized_path(request.path)
    for group in groups:
        if not group:
            continue
        try:
            iterable = list(group)
        except Exception:
            iterable = []
        for menu in iterable:
            for url in _collect_all_urls(menu):
                if _matches_path(current, _normalized_path(url)):
                    return "active"
    return ""


@register.simple_tag(takes_context=True)
def menu_open_children(context, menu):
    request = context.get("request")
    if not request or not menu:
        return ""
    current = _normalized_path(request.path)
    parent_url = menu.get("url") if isinstance(menu, dict) else getattr(menu, "url", "")
    if _matches_path(current, _normalized_path(parent_url)):
        return "menu-open"
    for url in _iter_descendant_urls(menu):
        if _matches_path(current, _normalized_path(url)):
            return "menu-open"
    return ""


@register.simple_tag(takes_context=True)
def menu_active_or_child(context, menu):
    request = context.get("request")
    if not request or not menu:
        return ""
    current = _normalized_path(request.path)
    parent_url = menu.get("url") if isinstance(menu, dict) else getattr(menu, "url", "")
    if _matches_path(current, _normalized_path(parent_url)):
        return "active"
    for url in _iter_descendant_urls(menu):
        if _matches_path(current, _normalized_path(url)):
            return "active"
    return ""


@register.simple_tag(takes_context=True)
def active_admin_exact(context, pattern):
    request = context.get("request")
    if not request or not pattern:
        return ""
    current = _normalized_path(request.path)
    target = _normalized_pattern(pattern, force_admin=current.startswith("/admin/"))
    if current == target:
        return "active"
    return ""


__all__ = [
    "dict_key",
    "dotformat",
    "active",
    "menu_open",
    "safe_menu_active",
    "safe_menu_open",
    "menu_group_open",
    "menu_group_active",
    "menu_open_children",
    "menu_active_or_child",
    "active_admin_exact",
]
