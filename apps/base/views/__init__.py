import bleach
from django.forms import fields
from django_summernote.widgets import SummernoteWidget
from django_summernote.settings import ALLOWED_TAGS, ATTRIBUTES

# ═══════════════════════════════════════════════════════════
# FaisalS | Version History App
# ═══════════════════════════════════════════════════════════

_original_bleach_clean = bleach.clean


def patched_bleach_clean(text, tags=None, attributes=None, styles=None, **kwargs):
    kwargs.pop("styles", None)

    if tags is None:
        tags = ALLOWED_TAGS
    if attributes is None:
        attributes = ATTRIBUTES

    return _original_bleach_clean(text, tags=tags, attributes=attributes, **kwargs)


bleach.clean = patched_bleach_clean


from django_summernote import fields as summernote_fields


class PatchedSummernoteTextFormField(fields.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.update({"widget": SummernoteWidget()})
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        return bleach.clean(value, tags=ALLOWED_TAGS, attributes=ATTRIBUTES)


summernote_fields.SummernoteTextFormField = PatchedSummernoteTextFormField
