from django.urls import path

from .views import (
    NoticeCreateView,
    NoticeDeleteView,
    NoticeDetailView,
    NoticeListView,
    NoticeUpdateView,
    add_notice_comment,
)

app_name = 'noticeboard'

urlpatterns = [
    path('', NoticeListView.as_view(), name='list'),
    path('create/', NoticeCreateView.as_view(), name='create'),
    path('<int:pk>/', NoticeDetailView.as_view(), name='detail'),
    path('<int:pk>/comment/', add_notice_comment, name='comment'),
    path('<int:pk>/edit/', NoticeUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', NoticeDeleteView.as_view(), name='delete'),
]
