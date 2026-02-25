from django.contrib import admin
from .models import LeaveRequest, LeaveType

admin.site.register(LeaveType)
admin.site.register(LeaveRequest)
