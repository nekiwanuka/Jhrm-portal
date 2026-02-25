from django.contrib import admin
from .models import ReportRequest, WeeklyReport

admin.site.register(ReportRequest)
admin.site.register(WeeklyReport)
