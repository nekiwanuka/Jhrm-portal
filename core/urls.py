from django.urls import path

from .views import (
    DashboardView,
    ExecutiveEmailView,
    PublicAccessCodeSettingsUpdateView,
    PublicAccessCodeView,
    PublicHomeView,
    StaffDashboardView,
    ThemeSettingsUpdateView,
)

app_name = 'core'

urlpatterns = [
    path('', PublicHomeView.as_view(), name='public_home'),
    path('access/', PublicAccessCodeView.as_view(), name='public_access'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/staff/', StaffDashboardView.as_view(), name='staff_dashboard'),
    path('tools/send-email/', ExecutiveEmailView.as_view(), name='send_email'),
    path('settings/theme/', ThemeSettingsUpdateView.as_view(), name='theme_settings'),
	path('settings/access-code/', PublicAccessCodeSettingsUpdateView.as_view(), name='access_code_settings'),
]
