from django.urls import path

from .views import (
    ClearSalaryVoucherView,
    EmployeePayItemCreateView,
    EmployeePayItemListView,
    EmployeePayItemUpdateView,
    PayItemTypeCreateView,
    PayItemTypeListView,
    PayItemTypeUpdateView,
    PayrollRunCreateView,
    PayrollRunDetailView,
    PayrollRunExportCSVView,
    PayrollRunListView,
    PenaltyCreateView,
    PenaltyListView,
    PenaltyUpdateView,
    SalaryStructureCreateView,
    SalaryStructureListView,
    SalaryStructureUpdateView,
)

app_name = 'payroll'

urlpatterns = [
    path('', PayrollRunListView.as_view(), name='list'),
    path('create/', PayrollRunCreateView.as_view(), name='create'),
    path('<int:pk>/', PayrollRunDetailView.as_view(), name='detail'),
    path('<int:pk>/export-cleared.csv', PayrollRunExportCSVView.as_view(), name='export_cleared_csv'),
    path('structures/', SalaryStructureListView.as_view(), name='structures'),
    path('structures/create/', SalaryStructureCreateView.as_view(), name='structure_create'),
    path('structures/<int:pk>/edit/', SalaryStructureUpdateView.as_view(), name='structure_edit'),
    path('pay-item-types/', PayItemTypeListView.as_view(), name='pay_item_types'),
    path('pay-item-types/create/', PayItemTypeCreateView.as_view(), name='pay_item_type_create'),
    path('pay-item-types/<int:pk>/edit/', PayItemTypeUpdateView.as_view(), name='pay_item_type_edit'),
    path('employee-pay-items/', EmployeePayItemListView.as_view(), name='employee_pay_items'),
    path('employee-pay-items/create/', EmployeePayItemCreateView.as_view(), name='employee_pay_item_create'),
    path('employee-pay-items/<int:pk>/edit/', EmployeePayItemUpdateView.as_view(), name='employee_pay_item_edit'),
    path('penalties/', PenaltyListView.as_view(), name='penalties'),
    path('penalties/create/', PenaltyCreateView.as_view(), name='penalty_create'),
    path('penalties/<int:pk>/edit/', PenaltyUpdateView.as_view(), name='penalty_edit'),
    path('payslips/<int:pk>/clear-voucher/', ClearSalaryVoucherView.as_view(), name='clear_voucher'),
]
