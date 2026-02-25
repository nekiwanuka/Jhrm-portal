from django.contrib import admin
from .models import Department, EmployeeDepartmentRole, EmployeeDocument, EmployeeProfile, Position

admin.site.register(Department)
admin.site.register(Position)
admin.site.register(EmployeeProfile)
admin.site.register(EmployeeDepartmentRole)
admin.site.register(EmployeeDocument)
