from django.contrib.auth.mixins import UserPassesTestMixin
from django.apps import apps


class HRAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER'}:
            return True
        if user.groups.filter(name__in={'Super Admin', 'HR Manager'}).exists():
            return True
        EmployeeDepartmentRole = apps.get_model('employees', 'EmployeeDepartmentRole')
        return EmployeeDepartmentRole.objects.filter(employee=user, is_active=True, role__code__in={'super-admin', 'hr-manager'}).exists()


class SupervisorPlusRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}:
            return True
        if user.groups.filter(name__in={'Super Admin', 'HR Manager', 'Supervisor'}).exists():
            return True
        EmployeeDepartmentRole = apps.get_model('employees', 'EmployeeDepartmentRole')
        return EmployeeDepartmentRole.objects.filter(employee=user, is_active=True, role__code__in={'super-admin', 'hr-manager', 'supervisor'}).exists()
