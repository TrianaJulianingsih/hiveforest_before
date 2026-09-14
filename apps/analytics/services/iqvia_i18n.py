from django.utils.translation import get_language

from apps.base.utils.translation import get_translation

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: iqvia_i18n                                          ║
# ║  Type: Service helper                                      ║
# ║  Purpose: One place the import module reads its wording    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_i18n.py               ║
# ║  Created: Sep/04-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# Every string on the IQVIA import page lives in this module code
MODULE = "analytics_import"


# One lookup in the language of the current request
def tr(key, default=None):
    return get_translation(MODULE, key, get_language() or "en", default)


# Same lookup, {name} placeholders filled from args
def tr_format(key, args=None, default=None):
    text = tr(key, default)
    for name, value in (args or {}).items():
        text = text.replace("{" + name + "}", str(value))
    return text


# Translated dimension name, the registry label stays the fallback
def dim_label(key, default=""):
    return tr("dim_" + key, default or key)


# Comma joined dimension names, used by every "upload X first" message
def dim_labels(keys, registry):
    return ", ".join(dim_label(k, registry[k]["label"]) for k in keys)


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: render_parts                                        ║
# ║  Type: Service helper                                      ║
# ║  Purpose: Turn message parts into one sentence             ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_i18n.py               ║
# ║  Created: Sep/04-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# A commit result carries parts, not a sentence. The sentence is built here
# for the immediate reply and rebuilt in the browser for the History tab,
# so an old row can still be read in a language nobody had chosen yet.
def render_parts(parts):
    return " ".join(
        tr_format("msg_" + part["code"], part.get("args") or {})
        for part in (parts or [])
    ).strip()


# One message part, kept tiny because every caller builds several
def part(code, **args):
    return {"code": code, "args": args}
