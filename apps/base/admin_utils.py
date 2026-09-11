from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.admin.actions import delete_selected
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django_currentuser.middleware import get_current_user
from django.utils.translation import ngettext
from django.contrib import admin
from django.utils.translation import gettext as _
from django.http import HttpResponseForbidden
from apps.base.models.permissions import Role
from apps.cms.models.appmanagers import ApplicationList
from django.db import transaction

csrf_protect_m = method_decorator(csrf_protect)

def delete_item(func):
    @csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        model = self.model
        if not obj:
            messages.error(request, "Object not found.")
            return redirect(reverse(f'admin:{model._meta.app_label}_{model._meta.model_name}_changelist'))

        if request.method == 'POST':  # If the user confirms deletion
            obj.deleted = True
            obj.dat = timezone.now()
            obj.dby = get_current_user()
            obj.save()
            self.log_deletion(request, obj, f"{obj}")
            messages.success(request, f"{model._meta.verbose_name} '{obj}' has been deleted.")
            return redirect(reverse(f'admin:{model._meta.app_label}_{model._meta.model_name}_changelist'))

        context = {
            'object': obj,
            'opts': model._meta,
            'title': f"Soft delete {model._meta.verbose_name}",
            'model_admin': self,
            'is_popup': False,
            'has_permission': self.has_delete_permission(request, obj),
        }
        return render(request, 'admin/delete_confirmation.html', context)

    return delete_view

class MassActionMixin:

    status_field = 'status'
    active_value = 1
    inactive_value = 0

    def activate_items(self, request, queryset):
        self._update_status(request, queryset, self.active_value, 'activated')

    activate_items.short_description = "Activate selected items"

    def deactivate_items(self, request, queryset):
        self._update_status(request, queryset, self.inactive_value, 'deactivated')

    deactivate_items.short_description = "Deactivate selected items"

    def _update_status(self, request, queryset, status_value, action_name):
        # Validate if the model has the specified status field
        if not hasattr(queryset.model, self.status_field):
            self.message_user(request, f"Model does not have field '{self.status_field}'.", messages.ERROR)
            return
        # Perform the bulk update
        with transaction.atomic():
            updated_count = queryset.update(**{self.status_field: status_value})

        # Provide feedback to the user
        # self.message_user(request, f"{updated_count} item(s) successfully {action_name}.", messages.SUCCESS)

        message = ngettext(
            f"{updated_count} {self.model._meta.verbose_name} item(s) successfully {action_name}.",
            f"{updated_count} {self.model._meta.verbose_name_plural} item(s) successfully {action_name}.",
            updated_count
        )
        messages.success(request, message)

    def delete_items(self, request, queryset):
        updated_count = queryset.update(deleted=True, dat=timezone.now(), dby=get_current_user())

        for obj in queryset:
            self.log_deletion(request, obj, f"{obj}")

        message = ngettext(
            f"Successfully deleted {updated_count} {self.model._meta.verbose_name}.",
            f"Successfully deleted {updated_count} {self.model._meta.verbose_name_plural}.",
            updated_count
        )
        messages.success(request, message)

    def restore_items(self, request, queryset):
        updated_count = queryset.update(deleted=False, dat=None, dby=None)

        for obj in queryset:
            self.log_deletion(request, obj, f"{obj}")

        message = ngettext(
            f"Successfully restored {updated_count} {self.model._meta.verbose_name}.",
            f"Successfully restored {updated_count} {self.model._meta.verbose_name_plural}.",
            updated_count
        )
        messages.success(request, message)

    def purge_items(self, request, queryset):
        self.purge_items(request, queryset)
    
    def get_actions(self, request):
        actions = super().get_actions(request)

        def activate_items_action(self, request, queryset):
                self.activate_items(request, queryset)
        def deactivate_items_action(self, request, queryset):
                self.deactivate_items(request, queryset)

        if 'delete_selected' in actions:
            del actions['delete_selected']
 
        def delete_items_action(self, request, queryset):
            self.delete_items(request, queryset)
        def restore_items_action(self, request, queryset):
            self.restore_items(request, queryset)

        actions['activate_items'] = (activate_items_action, 'activate_items', 'Activate selected %(verbose_name_plural)s item(s)')
        actions['deactivate_items'] = (deactivate_items_action, 'deactivate_items', 'Deactivate selected %(verbose_name_plural)s item(s)')

        actions['delete_items'] = (delete_items_action, 'delete_items', 'Mark selected %(verbose_name_plural)s as deleted')
        actions['restore_items'] = (restore_items_action, 'restore_items', 'Restore deleted %(verbose_name_plural)s')
        actions['delete_selected'] = (delete_selected, 'delete_selected', 'Purge %(verbose_name_plural)s')

        return actions

