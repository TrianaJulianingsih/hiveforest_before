from apps.base.services.system_log_service import SystemLogService
from apps.base.models.system_log import LogAction

class HumanCapitalViewLogMixin:
    """Mixin to automatically log list, detail, add, edit, and soft-delete requests in Human Capital."""
    def dispatch(self, request, *args, **kwargs):
        # Resolve model name
        model_name = getattr(self, 'model', None)
        model_str = model_name.__name__ if model_name else "Record"
        view_name = self.__class__.__name__

        if view_name == 'List':
            action = LogAction.READ
            description = f"User viewed {model_str} list page."
        elif view_name == 'Detail':
            action = LogAction.READ
            description = f"User viewed {model_str} details."
        elif view_name == 'Create':
            if request.method == 'POST':
                action = LogAction.CREATE
                description = f"User submitted new {model_str}."
            else:
                action = LogAction.READ
                description = f"User accessed {model_str} creation page."
        elif view_name == 'Update':
            if request.method == 'POST':
                action = LogAction.UPDATE
                description = f"User updated {model_str} details."
            else:
                action = LogAction.READ
                description = f"User accessed {model_str} edit page."
        elif view_name in ('SoftDel', 'SoftDelete'):
            action = LogAction.DELETE
            description = f"User deleted {model_str}."
        else:
            action = LogAction.READ
            description = f"User accessed {view_name} view for {model_str}."

        SystemLogService.log(
            request=request,
            action=action,
            module="Human Capital",
            feature=f"{model_str} {view_name}",
            description=description,
            log_type="SYSTEM"
        )
        return super().dispatch(request, *args, **kwargs)
