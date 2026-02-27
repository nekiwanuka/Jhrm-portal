from django.contrib.auth.mixins import UserPassesTestMixin
from django.apps import apps


def user_is_super_admin(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPER_ADMIN':
        return True
    try:
        if user.groups.filter(name__in={'Super Admin'}).exists():
            return True
    except Exception:
        pass
    EmployeeDepartmentRole = apps.get_model('employees', 'EmployeeDepartmentRole')
    return EmployeeDepartmentRole.objects.filter(employee=user, is_active=True, role__code__in={'super-admin'}).exists()


def user_is_hr_admin(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) in {'SUPER_ADMIN', 'HR_MANAGER'}:
        return True
    try:
        if user.groups.filter(name__in={'Super Admin', 'HR Manager'}).exists():
            return True
    except Exception:
        pass
    EmployeeDepartmentRole = apps.get_model('employees', 'EmployeeDepartmentRole')
    return EmployeeDepartmentRole.objects.filter(employee=user, is_active=True, role__code__in={'super-admin', 'hr-manager'}).exists()


def user_is_supervisor_plus(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}:
        return True
    try:
        if user.groups.filter(name__in={'Super Admin', 'HR Manager', 'Supervisor'}).exists():
            return True
    except Exception:
        pass
    EmployeeDepartmentRole = apps.get_model('employees', 'EmployeeDepartmentRole')
    return EmployeeDepartmentRole.objects.filter(employee=user, is_active=True, role__code__in={'super-admin', 'hr-manager', 'supervisor'}).exists()


class HRAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return user_is_hr_admin(self.request.user)


class SupervisorPlusRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return user_is_supervisor_plus(self.request.user)
