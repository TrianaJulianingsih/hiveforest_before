import json
import logging
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.db import connection, connections
from django.utils import timezone
from apps.base.models.system_log import SystemLog, LogAction, LogStatus
from apps.base.utils.authentication_utils import get_client_ip, parse_user_agent
from django_currentuser.middleware import get_current_authenticated_user

logger = logging.getLogger("apps.base.system_log")

# Background thread executor for async logging when in atomic block
_logging_executor = ThreadPoolExecutor(max_workers=2)
_thread_locals = threading.local()

def sanitize_payload(data):
    """Recursively mask sensitive keys in lists, dicts, or JSON-like strings."""
    if data is None:
        return None
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ['password', 'token', 'authorization', 'cookie', 'session', 'api_key', 'secret', 'private_key', 'csrf']):
                sanitized[k] = "******"
            else:
                sanitized[k] = sanitize_payload(v)
        return sanitized
    elif isinstance(data, (list, tuple, set)):
        return [sanitize_payload(item) for item in data]
    elif isinstance(data, (str, bytes)):
        # Try to parse stringified JSON and sanitize it
        try:
            parsed = json.loads(data)
            if isinstance(parsed, (dict, list)):
                return json.dumps(sanitize_payload(parsed))
        except Exception:
            pass
    return data

def serialize_field_val(val):
    """Safely serialize non-primitive types for JSON storage."""
    from datetime import date, datetime
    from decimal import Decimal
    import uuid
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, uuid.UUID):
        return str(val)
    try:
        json.dumps(val)
        return val
    except Exception:
        return str(val)

def clean_for_json(data):
    """Recursively clean dicts/lists to guarantee JSON-serializable primitives for db backends."""
    if data is None:
        return None
    if isinstance(data, dict):
        return {k: clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple, set)):
        return [clean_for_json(item) for item in data]
    return serialize_field_val(data)

def get_changes(old_dict, new_dict):
    """Generate a clean differential dictionary of changes for UPDATE actions."""
    changes = {}
    for key, val in new_dict.items():
        if key in ['uat', 'uby', 'updated_at', 'updated_by']:
            continue
        old_val = old_dict.get(key)
        if old_val != val:
            changes[key] = {
                "old": serialize_field_val(old_val),
                "new": serialize_field_val(val)
            }
    return changes

def _save_log_async(log_kwargs):
    """Save the log entry inside a background thread to bypass transaction rollbacks."""
    _thread_locals.is_logging = True
    try:
        SystemLog.objects.create(**log_kwargs)
    except Exception as e:
        logger.exception("Error saving SystemLog asynchronously: %s", e)
    finally:
        _thread_locals.is_logging = False
        for conn in connections.all():
            conn.close()

class SystemLogService:
    @staticmethod
    def log(
        request=None,
        action=None,
        module=None,
        feature=None,
        obj=None,
        description=None,
        old_data=None,
        new_data=None,
        status=LogStatus.SUCCESS,
        response_code=None,
        response_data=None,
        error_message=None,
        stack_trace=None,
        metadata=None,
        user=None,
        log_type=None,
        object_type=None,
        object_id=None,
    ):
        # 1. Guard against infinite recursive logging loop
        if getattr(_thread_locals, 'is_logging', False):
            return None

        _thread_locals.is_logging = True
        try:
            # 2. Retrieve request context if not explicitly passed
            from apps.base.middleware import RequestProviderMiddleware
            if not request:
                request = RequestProviderMiddleware.get_current_request()

            # 3. Retrieve user
            if not user:
                if request and getattr(request, 'user', None) and request.user.is_authenticated:
                    user = request.user
                else:
                    curr_user = get_current_authenticated_user()
                    if curr_user and curr_user.is_authenticated:
                        user = curr_user

            # 4. Resolve details from request
            ip_address = None
            user_agent = None
            request_method = None
            request_path = None
            if request:
                ip_address = get_client_ip(request)
                user_agent = request.META.get("HTTP_USER_AGENT", "")
                request_method = request.method
                request_path = request.path
                if not log_type and request_path.startswith('/api/'):
                    log_type = "API"

            # 5. Handle model object mapping
            if obj:
                if not object_type:
                    object_type = obj.__class__.__name__
                if not object_id:
                    object_id = str(obj.pk)

            # 6. Sanitize inputs to prevent storing credentials
            sanitized_old = sanitize_payload(old_data)
            sanitized_new = sanitize_payload(new_data)
            sanitized_meta = sanitize_payload(metadata)
            sanitized_resp = sanitize_payload(response_data)

            # Prepare log fields with clean json types
            log_kwargs = {
                "user": user,
                "action": action or LogAction.SYSTEM,
                "module": module,
                "feature": feature,
                "object_type": object_type,
                "object_id": object_id,
                "description": description,
                "status": status,
                "response_code": response_code,
                "response_data": str(sanitized_resp) if sanitized_resp is not None else None,
                "request_method": request_method,
                "request_path": request_path,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "old_data": clean_for_json(sanitized_old),
                "new_data": clean_for_json(sanitized_new),
                "error_message": error_message,
                "stack_trace": stack_trace,
                "metadata": clean_for_json(sanitized_meta),
                "log_type": log_type or "SYSTEM",
            }

            # 7. Asynchronous logging execution for transaction rollback safety
            is_sync = getattr(settings, 'SYSTEM_LOG_SYNC', False)
            if connection.in_atomic_block and not is_sync:
                _logging_executor.submit(_save_log_async, log_kwargs)
                return None
            else:
                return SystemLog.objects.create(**log_kwargs)

        except Exception as e:
            logger.exception("Error creating SystemLog entry: %s", e)
            return None
        finally:
            _thread_locals.is_logging = False

    @staticmethod
    def error(
        request=None,
        module=None,
        feature=None,
        error=None,
        stack_trace=None,
        log_type="SYSTEM",
        **kwargs
    ):
        """Standardized interface to log exception errors."""
        err_msg = str(error) if error else "Unknown error occurred"
        if not stack_trace:
            stack_trace = traceback.format_exc()
        
        if error and not module:
            module = error.__class__.__name__
        if not feature:
            feature = "System Error"

        description = kwargs.pop('description', f"Exception of type {error.__class__.__name__ if error else 'Error'}: {err_msg}")

        return SystemLogService.log(
            request=request,
            action=LogAction.ERROR,
            module=module,
            feature=feature,
            description=description,
            status=LogStatus.ERROR,
            error_message=err_msg,
            stack_trace=stack_trace,
            log_type=log_type,
            **kwargs
        )

    @staticmethod
    def log_bulk(
        action,
        model,
        affected_count,
        request=None,
        module=None,
        feature=None,
        description=None,
        metadata=None,
        **kwargs
    ):
        """Record bulk operations in a single consolidated audit entry."""
        model_name = model.__name__ if hasattr(model, '__name__') else str(model)
        if not module:
            module = model_name
        if not feature:
            feature = f"Bulk {action.replace('BULK_', '').title()}"
        if not description:
            description = f"Performed {action} on {affected_count} records of {model_name}."

        meta = metadata or {}
        meta['affected_records'] = affected_count

        return SystemLogService.log(
            request=request,
            action=action,
            module=module,
            feature=feature,
            object_type=model_name,
            description=description,
            status=LogStatus.SUCCESS,
            metadata=meta,
            **kwargs
        )
