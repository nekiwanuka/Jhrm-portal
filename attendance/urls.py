from django.urls import path

from .views import AttendanceCreateView, AttendanceListView

app_name = 'attendance'

urlpatterns = [
    path('', AttendanceListView.as_view(), name='list'),
    path('create/', AttendanceCreateView.as_view(), name='create'),
]
