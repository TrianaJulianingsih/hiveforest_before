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


from django.db import models

class SystemLogMixin:
    log_module = None
    log_feature = None

    def log_action(
        self,
        action,
        description=None,
        obj=None,
        old_data=None,
        new_data=None,
        status="SUCCESS",
        response_code=None,
        response_data=None,
        error_message=None,
        stack_trace=None,
        metadata=None,
        module=None,
        feature=None,
        user=None,
    ):
        """Allows Views, APIs, and Services to log specific events easily."""
        from apps.base.services.system_log_service import SystemLogService
        
        mod = module or self.log_module or getattr(self, 'module', getattr(self.__class__, '__name__', None))
        feat = feature or self.log_feature or getattr(self, 'feature', None)
        request = getattr(self, 'request', None)

        return SystemLogService.log(
            request=request,
            action=action,
            module=mod,
            feature=feat,
            obj=obj,
            description=description,
            old_data=old_data,
            new_data=new_data,
            status=status,
            response_code=response_code,
            response_data=response_data,
            error_message=error_message,
            stack_trace=stack_trace,
            metadata=metadata,
            user=user,
        )


class SystemLogModelMixin:
    """Automatically logs CREATE, UPDATE, and DELETE operations for mixed-in Models."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_values = self._get_instance_dict()

    def _get_instance_dict(self):
        if not self.pk:
            return {}
        data = {}
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey):
                data[field.name] = getattr(self, field.attname)
            else:
                data[field.name] = getattr(self, field.name)
        return data

    def save(self, *args, **kwargs):
        is_new = not self.pk
        old_data = {}
        if not is_new:
            if hasattr(self, '_original_values') and self._original_values:
                old_data = self._original_values
            else:
                try:
                    original = self.__class__.objects.get(pk=self.pk)
                    old_data = original._get_instance_dict()
                except self.__class__.DoesNotExist:
                    old_data = {}

        super().save(*args, **kwargs)
        new_data = self._get_instance_dict()

        from apps.base.services.system_log_service import SystemLogService, get_changes
        from apps.base.models.system_log import LogAction
        
        module_name = self._meta.app_label.title()
        feature_name = self._meta.verbose_name.title()

        if is_new:
            SystemLogService.log(
                action=LogAction.CREATE,
                module=module_name,
                feature=feature_name,
                obj=self,
                description=f"Created {self._meta.verbose_name} record.",
                new_data=new_data,
                status="SUCCESS"
            )
        else:
            changes = get_changes(old_data, new_data)
            if changes:
                SystemLogService.log(
                    action=LogAction.UPDATE,
                    module=module_name,
                    feature=feature_name,
                    obj=self,
                    description=f"Updated {self._meta.verbose_name} record.",
                    old_data=old_data,
                    new_data=new_data,
                    metadata={"changes": changes},
                    status="SUCCESS"
                )

        self._original_values = self._get_instance_dict()

    def delete(self, *args, **kwargs):
        old_data = self._get_instance_dict()
        super().delete(*args, **kwargs)

        from apps.base.services.system_log_service import SystemLogService
        from apps.base.models.system_log import LogAction
        
        module_name = self._meta.app_label.title()
        feature_name = self._meta.verbose_name.title()

        SystemLogService.log(
            action=LogAction.DELETE,
            module=module_name,
            feature=feature_name,
            obj=self,
            description=f"Deleted {self._meta.verbose_name} record.",
            old_data=old_data,
            status="SUCCESS"
        )

