"""
User-Assignment Utility Functions

Helper functions untuk relasi auth_user ↔ humancapital_assignment
Mempermudah akses dari User ke Assignment dan data terkait.

Usage:
    from apps.humancapital.utils import get_user_assignment, get_user_employee, get_user_site
    
    assignment = get_user_assignment(request.user)
    employee = get_user_employee(request.user)
    site = get_user_site(request.user)
"""

from django.contrib.auth.models import User
from django.db.models import Prefetch
from apps.humancapital.models.employee_models import Employee
from apps.humancapital.models.structure_models import Assignment


def get_user_person(user):
    """
    Get Person object dari User.
    
    Args:
        user: django.contrib.auth.models.User instance
    
    Returns:
        apps.base.models.people.Person or None
    """
    try:
        return user.userprofile.person
    except:
        return None


def get_user_employee(user, select_related=True):
    """
    Get Employee object dari User.
    
    Args:
        user: django.contrib.auth.models.User instance
        select_related: bool, untuk optimize query
    
    Returns:
        apps.humancapital.models.employee.Employee or None
    
    Example:
        employee = get_user_employee(request.user)
        if employee:
            print(employee.name)
    """
    # try:
    #     person = get_user_person(user)
    #     if not person:
    #         return None
        
    #     if select_related:
    #         return Employee.objects.select_related('person').get(person=person)
    #     else:
    #         return Employee.objects.get(person=person)
    # except Employee.DoesNotExist:
    #     return None
    try:
        qs = Employee.objects

        if select_related:
            qs = qs.select_related("user")

        return qs.get(user=user)
    except Employee.DoesNotExist:
        return None


def get_user_assignment(user, active_only=True, select_related=True):
    """
    Get Assignment object dari User (assignment pertama/terbaru).
    
    Args:
        user: django.contrib.auth.models.User instance
        active_only: bool, hanya assignment yang aktif (status=1, deleted=False)
        select_related: bool, untuk optimize query
    
    Returns:
        apps.humancapital.models.structure.Assignment or None
    
    Example:
        assignment = get_user_assignment(request.user)
        if assignment:
            print(f"Position: {assignment.position.name}")
            print(f"Site: {assignment.site.name}")
    """
    try:
        employee = get_user_employee(user, select_related=False)
        if not employee:
            return None
        
        queryset = Assignment.objects.filter(employee=employee)
        
        if active_only:
            queryset = queryset.filter(status=1, deleted=False)
        
        if select_related:
            queryset = queryset.select_related(
                'employee',
                'employee__user',
                'position',
                'title',
                'site'
            )
        
        return queryset.order_by('-effective', '-id').first()
    except:
        return None


def get_user_assignments(user, active_only=True, select_related=True):
    """
    Get all Assignment objects dari User.
    
    Args:
        user: django.contrib.auth.models.User instance
        active_only: bool, hanya assignment yang aktif
        select_related: bool, untuk optimize query
    
    Returns:
        QuerySet of apps.humancapital.models.structure.Assignment
    
    Example:
        assignments = get_user_assignments(request.user)
        for assignment in assignments:
            print(assignment.position.name)
    """
    try:
        employee = get_user_employee(user, select_related=False)
        if not employee:
            return Assignment.objects.none()
        
        queryset = Assignment.objects.filter(employee=employee)
        
        if active_only:
            queryset = queryset.filter(status=1, deleted=False)
        
        if select_related:
            queryset = queryset.select_related(
                'employee',
                'employee__user',
                'position',
                'title',
                'site'
            )
        
        return queryset.order_by('-effective', '-id')
    except:
        return Assignment.objects.none()


def get_user_site(user):
    """
    Get Site object dari Assignment user.
    
    Args:
        user: django.contrib.auth.models.User instance
    
    Returns:
        apps.base.models.sites.Sites or None
    
    Example:
        site = get_user_site(request.user)
        if site:
            print(f"Site: {site.name}")
    """
    assignment = get_user_assignment(user)
    if assignment and assignment.site:
        return assignment.site
    return None


def get_user_site_id(user):
    """
    Get Site ID dari Assignment user.
    
    Args:
        user: django.contrib.auth.models.User instance
    
    Returns:
        int: site_id from assignment, None if no assignment
        NOTE: Returns actual site_id regardless of is_staff/is_superuser
    
    Example:
        site_id = get_user_site_id(request.user)
        if site_id == 1:
            # User has full access (site_id=1)
        elif site_id:
            # User has filtered access (specific site)
    """
    site = get_user_site(user)
    return site.id if site else None


def get_user_position(user):
    """
    Get Position object dari Assignment user.
    
    Args:
        user: django.contrib.auth.models.User instance
    
    Returns:
        apps.humancapital.models.structure.Position or None
    """
    assignment = get_user_assignment(user)
    if assignment:
        return assignment.position
    return None


def get_user_organization(user):
    """
    Get Organization object dari Position → Assignment user.
    
    Args:
        user: django.contrib.auth.models.User instance
    
    Returns:
        apps.humancapital.models.structure.Organization or None
    """
    position = get_user_position(user)
    if position:
        return position.organization
    return None


def get_user_assignment_info(user):
    """
    Get complete assignment info dict dari User.
    
    Args:
        user: django.contrib.auth.models.User instance
    
    Returns:
        dict dengan keys: user, person, employee, assignment, position, organization, site
    
    Example:
        info = get_user_assignment_info(request.user)
        print(info['position'].name)
        print(info['site'].name)
    """
    # person = get_user_person(user)
    # employee = get_user_employee(user) if person else None
    # assignment = get_user_assignment(user) if employee else None
    employee = get_user_employee(user)
    assignment = get_user_assignment(user)
    
    return {
        'user': user,
        # 'person': person,
        'employee': employee,
        'assignment': assignment,
        'position': assignment.position if assignment else None,
        'organization': assignment.position.organization if assignment and assignment.position else None,
        'site': assignment.site if assignment else None,
    }


def is_user_admin_or_manager(user):
    """
    Check apakah user adalah admin atau manager (title_id=3).
    
    Args:
        user: django.contrib.auth.models.User instance
    
    Returns:
        bool: True jika admin atau manager
    """
    if user.is_superuser or user.is_staff:
        return True
    
    assignment = get_user_assignment(user)
    return assignment and assignment.title_id == 3


def prefetch_user_with_assignment(queryset):
    """
    Optimize User queryset dengan prefetch assignment.
    
    Args:
        queryset: QuerySet of django.contrib.auth.models.User
    
    Returns:
        QuerySet dengan prefetch_related assignment
    
    Example:
        users = prefetch_user_with_assignment(User.objects.all())
        for user in users:
            assignment = get_user_assignment(user)  # No extra query
    """
    from django.db.models import Prefetch
    
    return queryset.prefetch_related(
        Prefetch(
            # 'userprofile__person__employee__assignment_set',
            'employee__assignment_set',
            queryset=Assignment.objects.select_related(
                'position',
                'title',
                'site'
            ).filter(status=1, deleted=False)
        )
    )
