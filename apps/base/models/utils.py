from django_currentuser.middleware import get_current_authenticated_user
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.models import Group
from apps.base.models import Role
from apps.supplychain.models import Distributor, Branch
from apps.base.models import SCMPermission
from django.db.models import Q

def get_filtered_model(user, model, permission_model, *args, **kwargs):
    """
    Filters a given model based on user permissions dynamically.

    Args:
        user: The user to filter permissions for.
        model: The model to filter (e.g., OrderHeader, Product, Invoice).
        permission_model: The permission model to use for filtering (e.g., SCMPermission, CMSPermission).
        *args: List of permission-related fields (e.g., 'distributor', 'branch').
        **kwargs: Custom field mappings (e.g., distributor_field='distributor', branch_field='orderbranch').

    Returns:
        QuerySet: A filtered QuerySet for the given model.
    """
    # Fetch roles for the user
    groups = Group.objects.filter(user=user)
    roles = Role.objects.filter(user=user) | Role.objects.filter(group__in=groups)

    if not roles.exists():
        return model.objects.none()

    # Permission checks for each field in args
    filters = {}
    for field in args:
        state_key = f"{field}_state"  # e.g., 'branch_state'
        model_field = kwargs.get(f"{field}_field", field)  # Default to field if no mapping provided
        related_model = kwargs.get(f"{field}_related_model")  # Related model for `allow_all`

        # Fetch permissions for the field
        field_perms = permission_model.objects.filter(role__in=roles)
        allow_all = field_perms.filter(**{state_key: 'allow_all'}).exists()

        if allow_all:
            if not related_model:
                raise ValueError(f"Missing related model for field '{field}'.")
            filters[f"{model_field}__id__in"] = related_model.objects.values_list('id', flat=True)
        else:
            specific_ids = field_perms.filter(**{state_key: 'allow'}).values_list(f"{field}__id", flat=True).distinct()
            filters[f"{model_field}__id__in"] = specific_ids

    # Apply the filters to the model
    return model.objects.filter(**filters)

def get_permitted_distributors(user):
    if user is None or not hasattr(user, 'is_authenticated'):
        return Distributor.objects.none()
    
    if user.is_authenticated:
        groups = Group.objects.filter(user=user)
        roles = Role.objects.filter(user=user) | Role.objects.filter(group__in=groups)

        # Check if the user has a role that allows access to all distributors
        if SCMPermission.objects.filter(role__in=roles, distributor_state='allow_all').exists():
            return Distributor.objects.all()

        # Otherwise, filter by specific permissions
        permitted_ids = SCMPermission.objects.filter(role__in=roles).values_list('distributor', flat=True)
        return Distributor.objects.filter(id__in=permitted_ids)
    return Distributor.objects.none()

def get_permitted_branches(user):
    if user is None or not hasattr(user, 'is_authenticated'):
        return Branch.objects.none()
    
    if user.is_authenticated:
        groups = Group.objects.filter(user=user)
        roles = Role.objects.filter(user=user) | Role.objects.filter(group__in=groups)

        # Check if the user has a role that allows access to all branches
        if SCMPermission.objects.filter(role__in=roles, branch_state='allow_all').exists():
            return Branch.objects.all()

        # Otherwise, filter by specific permissions
        permitted_ids = SCMPermission.objects.filter(role__in=roles).values_list('branch', flat=True)
        return Branch.objects.filter(id__in=permitted_ids)
    return Branch.objects.none()

def prepare_import(row, model):
    if not model.objects.filter(code=row['code']).exists():
        row['id'] = None
    if not model.objects.filter(status=row['status']).exists():
        row['status'] = 1

def set_cby_uby(instance, is_new, user=None):
    user = get_current_authenticated_user()
    if is_new:  # On create
        if user:
            instance.cby = user
        instance.uat = None  # No 'updated at' on creation
        instance.uby = None  # No 'updated by' on creation
    else:  # On update
        if user:
            instance.uby = user
        instance.uat = timezone.now()  # Always update 'updated at'

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_or_filter                                     ║
# ║  Purpose: Use '|' character as OR in column filter         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\mdeles\utils.py                           ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updated: May/15-2025                                      ║
# ╚════════════════════════════════════════════════════════════╝
def build_or_filter(field_lookup, values):
    q_objects = Q()
    for val in values.split("|"):
        val = val.strip()
        if val:
            q_objects |= Q(**{field_lookup: val})
    return q_objects


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: toggle_status                                       ║
# ║  Purpose: Used in many table to toggle record status       ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\models\utils.py                           ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updated: May/15-2025                                      ║
# ╚════════════════════════════════════════════════════════════╝
def toggle_status(instance, user, status_field='status', updated_by_field='uby', updated_at_field='uat'):
    """
    Toggle the status field of a model instance and update metadata fields.
    
    Args:
        instance: Model instance with a status field (0/1 or True/False).
        user: The request.user performing the update.
        status_field: Name of the status field (default: 'status').
        updated_by_field: Name of the updated_by field (default: 'uby').
        updated_at_field: Name of the updated_at field (default: 'uat').
        
    Returns:
        A tuple of (new_status, label), e.g., (1, 'activated')
    """
    current_status = getattr(instance, status_field)
    new_status = 0 if current_status == 1 else 1
    label = "deactivated" if new_status == 0 else "activated"

    setattr(instance, status_field, new_status)
    setattr(instance, updated_by_field, user)
    setattr(instance, updated_at_field, timezone.now())
    instance.save(update_fields=[status_field, updated_by_field, updated_at_field])

    return new_status, label

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: soft_delete                                         ║
# ║  Purpose: Used in many table to soft-delete record         ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\models\utils.py                           ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updated: May/19-2025                                      ║
# ╚════════════════════════════════════════════════════════════╝
def soft_delete(obj, user=None, cascade=None):
    """
    Soft delete an object by setting `deleted=True`, `deleted_at`, and `deleted_by`.
    Optionally cascade delete related objects by field name.

    Args:
        obj: The model instance to soft delete.
        user: The user performing the delete (optional).
        cascade: List of related field names to also soft delete.
    
    Returns:
        bool: True if deletion was performed, False if already deleted.
    """
    if getattr(obj, 'deleted', False):
        return False  # Already deleted

    obj.deleted = True

    if hasattr(obj, 'dat'):
        obj.dat = now()

    if user and hasattr(obj, 'dby'):
        obj.dby = user

    obj.save()

    if cascade:
        for field_name in cascade:
            related = getattr(obj, field_name, None)
            if related:
                if isinstance(related, list) or hasattr(related, 'all'):  # Reverse FK or M2M
                    for item in related.all():
                        soft_delete(item, user=user)
                else:
                    soft_delete(related, user=user)

    return True

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_nested_attr                                     ║
# ║  Type: Utility Function                                    ║
# ║  Purpose: Takes an object and a field string               ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\models\utils.py                           ║
# ║  Created: May/16-2025 by Setiadji                          ║
# ║  Updated: May/27-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
def get_nested_attr(obj, attr_path, default=None):
    try:
        for attr in attr_path.split("__"):
            obj = getattr(obj, attr)
            if obj is None:
                return default
        return obj
    except AttributeError:
        return default