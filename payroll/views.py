from decimal import Decimal
import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView, DetailView

from core.permissions import HRAdminRequiredMixin

from employees.models import EmployeeProfile

from .forms import EmployeePayItemForm, PayrollRunForm, PayItemTypeForm, PenaltyForm, SalaryStructureForm
from .models import EmployeePayItem, PayItemType, PayrollRun, Payslip, Penalty, SalaryStructure, SalaryVoucher


def _month_bounds(month_start):
	month_start = month_start.replace(day=1)
	if month_start.month == 12:
		next_month = month_start.replace(year=month_start.year + 1, month=1, day=1)
	else:
		next_month = month_start.replace(month=month_start.month + 1, day=1)
	month_end = next_month - timedelta(days=1)
	return month_start, month_end


def _employee_identifier(user):
	try:
		profile = user.employee_profile
		if profile.employee_id:
			return profile.employee_id
	except Exception:
		pass
	return user.username


def compute_payslip(run, employee, *, created_by=None):
	month_start, month_end = _month_bounds(run.month)

	structure = getattr(employee, 'salary_structure', None)
	if not structure or not structure.is_active:
		return None

	base_salary = structure.basic_salary
	legacy_allowances = structure.allowances
	legacy_deductions = structure.deductions

	items = EmployeePayItem.objects.select_related('item_type').filter(employee=employee, is_active=True, item_type__is_active=True)
	items = items.filter(
		models.Q(start_date__isnull=True) | models.Q(start_date__lte=month_end),
		models.Q(end_date__isnull=True) | models.Q(end_date__gte=month_start),
	)

	allowance_total = Decimal('0.00')
	deduction_total = Decimal('0.00')
	for item in items:
		if item.item_type.kind == item.item_type.KIND_ALLOWANCE:
			allowance_total += item.amount
		else:
			deduction_total += item.amount

	penalties = Penalty.objects.filter(employee=employee, applies_to_month=run.month)
	penalty_total = penalties.filter(status=Penalty.STATUS_CLEARED).aggregate(models.Sum('amount')).get('amount__sum') or Decimal('0.00')
	penalties_pending = penalties.filter(status=Penalty.STATUS_PENDING).exists()

	gross = base_salary + legacy_allowances + allowance_total
	deductions = legacy_deductions + deduction_total + penalty_total
	taxable = max(gross - deductions, Decimal('0.00'))
	tax = (taxable * Decimal('0.10')).quantize(Decimal('0.01'))
	net = gross - deductions - tax

	payslip, _created = Payslip.objects.update_or_create(
		payroll_run=run,
		employee=employee,
		defaults={
			'basic_salary': base_salary,
			'allowance_total': legacy_allowances + allowance_total,
			'deduction_total': legacy_deductions + deduction_total,
			'penalty_total': penalty_total,
			'gross_pay': gross,
			'tax_amount': tax,
			'net_pay': net,
			'is_held': penalties_pending,
		},
	)

	voucher_number = f"SV-{run.month:%Y%m}-{_employee_identifier(employee)}"
	voucher_defaults = {
		'voucher_number': voucher_number,
		'status': SalaryVoucher.STATUS_ON_HOLD if payslip.is_held else SalaryVoucher.STATUS_CLEARED,
	}
	voucher, _voucher_created = SalaryVoucher.objects.update_or_create(payslip=payslip, defaults=voucher_defaults)
	if voucher.status == SalaryVoucher.STATUS_CLEARED and not voucher.cleared_at:
		voucher.cleared_by = created_by
		voucher.cleared_at = timezone.now()
		voucher.save(update_fields=['cleared_by', 'cleared_at'])
	if voucher.status == SalaryVoucher.STATUS_ON_HOLD:
		SalaryVoucher.objects.filter(pk=voucher.pk).update(cleared_by=None, cleared_at=None)

	return payslip


class PayrollRunListView(LoginRequiredMixin, HRAdminRequiredMixin, ListView):
	model = PayrollRun
	template_name = 'payroll/payroll_run_list.html'
	context_object_name = 'payroll_runs'
	ordering = ['-month']


class PayrollRunCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = PayrollRun
	form_class = PayrollRunForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:list')

	def form_valid(self, form):
		form.instance.created_by = self.request.user
		form.instance.month = form.cleaned_data['month'].replace(day=1)
		response = super().form_valid(form)
		run = self.object
		with transaction.atomic():
			for structure in SalaryStructure.objects.select_related('employee').filter(is_active=True):
				compute_payslip(run, structure.employee, created_by=self.request.user)
		messages.success(self.request, 'Payroll run created and payslips generated.')
		return response


class PayrollRunDetailView(LoginRequiredMixin, HRAdminRequiredMixin, DetailView):
	model = PayrollRun
	template_name = 'payroll/payroll_run_detail.html'
	context_object_name = 'run'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['payslips'] = self.object.payslips.select_related('employee').order_by('employee__username')
		return context


class PayrollRunExportCSVView(LoginRequiredMixin, HRAdminRequiredMixin, View):
	def get(self, request, pk):
		run = get_object_or_404(PayrollRun, pk=pk)
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = f'attachment; filename="payroll_{run.month:%Y_%m}_cleared.csv"'
		writer = csv.writer(response)
		writer.writerow(['Employee', 'Employee ID', 'Bank Name', 'Account Number', 'Branch', 'Net Pay', 'Voucher Number'])

		payslips = (
			Payslip.objects.select_related('employee', 'salary_voucher')
			.filter(payroll_run=run, salary_voucher__status=SalaryVoucher.STATUS_CLEARED)
			.order_by('employee__username')
		)
		profiles = {p.user_id: p for p in EmployeeProfile.objects.filter(user__in=[ps.employee for ps in payslips])}

		for ps in payslips:
			profile = profiles.get(ps.employee_id)
			employee_id = getattr(profile, 'employee_id', '') if profile else ''
			bank_name = getattr(profile, 'bank_name', '') if profile else ''
			account_number = getattr(profile, 'bank_account_number', '') if profile else ''
			branch = getattr(profile, 'bank_branch', '') if profile else ''
			writer.writerow([
				ps.employee.get_full_name() or ps.employee.username,
				employee_id,
				bank_name,
				account_number,
				branch,
				str(ps.net_pay),
				ps.salary_voucher.voucher_number,
			])
		return response


class SalaryStructureListView(LoginRequiredMixin, HRAdminRequiredMixin, ListView):
	model = SalaryStructure
	template_name = 'payroll/salary_structure_list.html'
	context_object_name = 'structures'
	ordering = ['employee__username']


class SalaryStructureCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = SalaryStructure
	form_class = SalaryStructureForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:structures')


class SalaryStructureUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = SalaryStructure
	form_class = SalaryStructureForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:structures')


class PayItemTypeListView(LoginRequiredMixin, HRAdminRequiredMixin, ListView):
	model = PayItemType
	template_name = 'payroll/pay_item_type_list.html'
	context_object_name = 'types'
	ordering = ['kind', 'name']


class PayItemTypeCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = PayItemType
	form_class = PayItemTypeForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:pay_item_types')


class PayItemTypeUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = PayItemType
	form_class = PayItemTypeForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:pay_item_types')


class EmployeePayItemListView(LoginRequiredMixin, HRAdminRequiredMixin, ListView):
	model = EmployeePayItem
	template_name = 'payroll/employee_pay_item_list.html'
	context_object_name = 'items'
	ordering = ['employee__username', 'item_type__kind', 'item_type__name']

	def get_queryset(self):
		return EmployeePayItem.objects.select_related('employee', 'item_type').all()


class EmployeePayItemCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = EmployeePayItem
	form_class = EmployeePayItemForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:employee_pay_items')

	def form_valid(self, form):
		form.instance.created_by = self.request.user
		return super().form_valid(form)


class EmployeePayItemUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = EmployeePayItem
	form_class = EmployeePayItemForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:employee_pay_items')


class PenaltyListView(LoginRequiredMixin, HRAdminRequiredMixin, ListView):
	model = Penalty
	template_name = 'payroll/penalty_list.html'
	context_object_name = 'penalties'
	ordering = ['-applies_to_month', '-incident_date']


class PenaltyCreateView(LoginRequiredMixin, HRAdminRequiredMixin, CreateView):
	model = Penalty
	form_class = PenaltyForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:penalties')

	def form_valid(self, form):
		form.instance.created_by = self.request.user
		form.instance.applies_to_month = form.cleaned_data['applies_to_month'].replace(day=1)
		response = super().form_valid(form)
		if self.object.status in {Penalty.STATUS_CLEARED, Penalty.STATUS_WAIVED}:
			self.object.cleared_by = self.request.user
			self.object.cleared_at = timezone.now()
			self.object.save(update_fields=['cleared_by', 'cleared_at'])
		return response


class PenaltyUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = Penalty
	form_class = PenaltyForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('payroll:penalties')

	def form_valid(self, form):
		form.instance.applies_to_month = form.cleaned_data['applies_to_month'].replace(day=1)
		response = super().form_valid(form)
		if self.object.status in {Penalty.STATUS_CLEARED, Penalty.STATUS_WAIVED} and not self.object.cleared_at:
			self.object.cleared_by = self.request.user
			self.object.cleared_at = timezone.now()
			self.object.save(update_fields=['cleared_by', 'cleared_at'])
		if self.object.status == Penalty.STATUS_PENDING:
			Penalty.objects.filter(pk=self.object.pk).update(cleared_by=None, cleared_at=None)
		return response


class ClearSalaryVoucherView(LoginRequiredMixin, HRAdminRequiredMixin, View):
	def post(self, request, pk):
		payslip = get_object_or_404(Payslip.objects.select_related('payroll_run', 'employee'), pk=pk)
		run = payslip.payroll_run
		if run.locked:
			messages.error(request, 'Payroll run is locked.')
			return redirect(reverse('payroll:detail', kwargs={'pk': run.pk}))

		pending_penalties = Penalty.objects.filter(employee=payslip.employee, applies_to_month=run.month, status=Penalty.STATUS_PENDING).exists()
		if pending_penalties:
			messages.error(request, 'Cannot clear salary voucher: employee has pending penalties for this month.')
			return redirect(reverse('payroll:detail', kwargs={'pk': run.pk}))

		with transaction.atomic():
			compute_payslip(run, payslip.employee, created_by=request.user)
			SalaryVoucher.objects.filter(payslip=payslip).update(status=SalaryVoucher.STATUS_CLEARED, cleared_by=request.user, cleared_at=timezone.now())
		messages.success(request, 'Salary voucher cleared.')
		return redirect(reverse('payroll:detail', kwargs={'pk': run.pk}))
