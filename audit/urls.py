from django.urls import path

from .views import (
    AuditLogListView,
    NotificationListView,
    mark_all_notifications_read,
    mark_notification_read,
)

app_name = 'audit'

urlpatterns = [
    path('', AuditLogListView.as_view(), name='log_list'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='notifications_mark_all_read'),
    path('notifications/<int:pk>/read/', mark_notification_read, name='notifications_mark_read'),
]
