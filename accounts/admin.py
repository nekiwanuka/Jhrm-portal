from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import BusinessRole, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
	fieldsets = UserAdmin.fieldsets + (
		('HR Fields', {'fields': ('role', 'phone_number')}),
	)
	list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')


@admin.register(BusinessRole)
class BusinessRoleAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'department_scope', 'approval_authority_level', 'financial_authorization_limit', 'is_active')
	list_filter = ('is_active', 'department_scope')
	search_fields = ('code', 'name')
