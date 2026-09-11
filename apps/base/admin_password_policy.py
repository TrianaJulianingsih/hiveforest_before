from django.contrib import admin
from django.utils.translation import get_language
from apps.base.models.password_policy import PasswordPolicy
from apps.base.utils.translation import get_module_translations


# ═══════════════════════════════════════════════════════════
# FaisalS | Password Policy
# ═══════════════════════════════════════════════════════════
@admin.register(PasswordPolicy)
class PasswordPolicyAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        from django.contrib.admin.views.main import ChangeList

        class TranslatedChangeList(ChangeList):
            def get_headers(inner_self):
                headers = super().get_headers()
                current_lang = get_language() or "en"
                t = get_module_translations("password_policy", current_lang)
                label_map = {
                    "min_length": "min_length_label",
                    "max_length": "max_length_label",
                    "require_lowercase": "require_lowercase_label",
                    "require_uppercase": "require_uppercase_label",
                    "require_number": "require_number_label",
                    "require_special": "require_special_label",
                    "require_space": "require_space_label",
                    "updated_at": "updated_at_label",
                }
                for h in headers:
                    if h["text"] in label_map:
                        h["text"] = t.get(label_map[h["text"]], h["text"])
                return headers

        return TranslatedChangeList

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        current_lang = get_language() or "en"
        t = get_module_translations("password_policy", current_lang)

        label_map = {
            "min_length": "min_length_label",
            "max_length": "max_length_label",
            "require_lowercase": "require_lowercase_label",
            "require_uppercase": "require_uppercase_label",
            "require_number": "require_number_label",
            "require_special": "require_special_label",
            "require_space": "require_space_label",
        }

        for field, key in label_map.items():
            if field in form.base_fields:
                form.base_fields[field].label = t.get(
                    key, form.base_fields[field].label
                )

        return form

    list_display = (
        "min_length",
        "require_number",
        "require_uppercase",
        "require_special",
        "updated_at",
    )
    list_display_links = ("min_length",)
    list_editable = ("require_number", "require_uppercase", "require_special")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not PasswordPolicy.objects.exists()
