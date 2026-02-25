from django.urls import path

from .views import (
    LeaveRequestApprovalView,
    LeaveRequestCreateView,
    LeaveRequestListView,
    LeaveOfferLetterView,
    LeaveTypeCreateView,
    LeaveTypeListView,
    LeaveTypeUpdateView,
)

app_name = 'leave_mgmt'

urlpatterns = [
    path('', LeaveRequestListView.as_view(), name='list'),
    path('create/', LeaveRequestCreateView.as_view(), name='create'),
    path('<int:pk>/approve/', LeaveRequestApprovalView.as_view(), name='approve'),
	path('<int:pk>/letter/', LeaveOfferLetterView.as_view(), name='letter'),
    path('types/', LeaveTypeListView.as_view(), name='type_list'),
    path('types/create/', LeaveTypeCreateView.as_view(), name='type_create'),
    path('types/<int:pk>/edit/', LeaveTypeUpdateView.as_view(), name='type_edit'),
]
