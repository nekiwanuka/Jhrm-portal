from django.urls import path

from .views import EventCalendarView, EventCreateView, EventDeleteView, EventUpdateView

app_name = 'calendar_app'

urlpatterns = [
    path('', EventCalendarView.as_view(), name='month'),
    path('create/', EventCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', EventUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', EventDeleteView.as_view(), name='delete'),
]
