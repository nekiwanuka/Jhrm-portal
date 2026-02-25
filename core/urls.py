from django.urls import path

from .views import (
    DashboardView,
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
    path('settings/theme/', ThemeSettingsUpdateView.as_view(), name='theme_settings'),
	path('settings/access-code/', PublicAccessCodeSettingsUpdateView.as_view(), name='access_code_settings'),
]
