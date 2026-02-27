from django.urls import path

from .views import (
    DashboardView,
    ExecutiveEmailView,
    InboxDetailView,
    InboxListView,
    UserManualPdfView,
	UserManualStaffPdfView,
    PublicAccessCodeSettingsUpdateView,
    PublicAccessCodeView,
    PublicHomeView,
    GlobalSearchView,
    StaffDashboardView,
    ThemeSettingsUpdateView,
)

app_name = 'core'

urlpatterns = [
    path('', PublicHomeView.as_view(), name='public_home'),
    path('access/', PublicAccessCodeView.as_view(), name='public_access'),
	path('search/', GlobalSearchView.as_view(), name='search'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/staff/', StaffDashboardView.as_view(), name='staff_dashboard'),
    path('tools/send-email/', ExecutiveEmailView.as_view(), name='send_email'),
    path('tools/inbox/', InboxListView.as_view(), name='inbox'),
    path('tools/inbox/<int:pk>/', InboxDetailView.as_view(), name='inbox_detail'),
    path('help/user-manual.pdf', UserManualPdfView.as_view(), name='user_manual_pdf'),
	path('help/user-manual-staff.pdf', UserManualStaffPdfView.as_view(), name='user_manual_staff_pdf'),
    path('settings/theme/', ThemeSettingsUpdateView.as_view(), name='theme_settings'),
	path('settings/access-code/', PublicAccessCodeSettingsUpdateView.as_view(), name='access_code_settings'),
]
