from django.urls import path

from .views import (
    ReportCSVExportView,
    ReportRequestCreateView,
    ReportRequestDetailView,
    ReportRequestListView,
    WeeklyReportCreateView,
    WeeklyReportDetailView,
    WeeklyReportListView,
)

app_name = 'reports'

urlpatterns = [
    path('', ReportRequestListView.as_view(), name='list'),
    path('create/', ReportRequestCreateView.as_view(), name='create'),
    path('<int:pk>/', ReportRequestDetailView.as_view(), name='detail'),
    path('export/csv/', ReportCSVExportView.as_view(), name='export_csv'),
	path('weekly/', WeeklyReportListView.as_view(), name='weekly_list'),
    path('weekly/<int:pk>/', WeeklyReportDetailView.as_view(), name='weekly_detail'),
	path('weekly/submit/', WeeklyReportCreateView.as_view(), name='weekly_submit'),
]
