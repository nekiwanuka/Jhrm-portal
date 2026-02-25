from django.urls import path

from .views import PerformanceReviewCreateView, PerformanceReviewListView

app_name = 'performance'

urlpatterns = [
    path('', PerformanceReviewListView.as_view(), name='list'),
    path('create/', PerformanceReviewCreateView.as_view(), name='create'),
]
