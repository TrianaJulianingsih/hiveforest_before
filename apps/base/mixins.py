from django.utils.text import slugify
from django.urls import reverse_lazy
from django.conf import settings

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: ModelMetadataMixin                                  ║
# ║  Purpose: Generic mixin to pass model metadata             ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\employees_views.py          ║
# ║  Created: May/15-2025 by Setiadji                          ║
# ║  Updated: May/27-025 by Setiadji                           ║
# ╚════════════════════════════════════════════════════════════╝
class ModelMetadataMixin:
    namespace = None
    model = None

    def get_namespace(self):
        return f"{self.namespace}:" if self.namespace else ""
    
    def get_model_slug(self):
        # Slug from model's verbose_name_plural, fallback to model_name
        if self.model:
            return slugify(self.model._meta.verbose_name_plural).lower()
        return ""
    
    @property
    def add_url(self):
        # Compose the url name with namespace and model slug + action
        url_name = f"{self.get_namespace()}{self.get_model_slug()}-add"  # e.g. 'humancapital:employees-add'
        return reverse_lazy(url_name)

    def get_model_meta(self):
        if not self.model:
            return {}
        meta = self.model._meta
        slug = slugify(meta.verbose_name).lower()
        return {
            'verbose_name': meta.verbose_name.title(),
            'verbose_name_plural': meta.verbose_name_plural.title(),
            'slug': slug,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meta = self.get_model_meta()
        namespace_prefix = self.get_namespace()
        context.update({
            'page_title': f"{getattr(settings, 'PROJECT_NAME', '')} | {meta.get('verbose_name_plural', '')} List",
            'card_title': f"{meta.get('verbose_name_plural', '')} List",
            'add_url': reverse_lazy(f'{namespace_prefix}{meta.get("slug", "")}-add'),
            'custom_js': f'custom/js/{meta.get("slug", "")}_list.js',
            'table_id': f'{meta.get("slug", "")}_table',
            'tbody_id': f'{meta.get("slug", "")}-list-body',
        })
        return context
    
# ╔════════════════════════════════════════════════════════════╗
# ║  Name: BatchFieldMixin                                     ║
# ║  Purpose: Generic mixin to build batch-update              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\views\employees_views.py          ║
# ║  Created: May/15-2025 by Setiadji                          ║
# ║  Updated:                                                  ║
# ╚════════════════════════════════════════════════════════════╝
class BatchFieldMixin:
    # default batch fields available for all
    batch_fields = [
        {
            'name': 'status',
            'label': 'Status',
            'options': ['Active', 'Inactive', '__blank__']
        }
    ]

    def get_batch_fields(self):
        # Allow views to override or extend this
        return self.batch_fields
