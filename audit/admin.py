from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
	list_display = ('created_at', 'user', 'method', 'path', 'status_code')
	list_filter = ('method', 'status_code', 'created_at')
	search_fields = ('path', 'action', 'user__username')
