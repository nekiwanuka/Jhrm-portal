from django.conf import settings
from django.db import models
from django.utils import timezone


class SalaryStructure(models.Model):
	employee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='salary_structure')
	basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
	allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	currency = models.CharField(max_length=10, default='UGX')
	effective_from = models.DateField(null=True, blank=True)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return f'Salary - {self.employee}'


class PayItemType(models.Model):
	KIND_ALLOWANCE = 'ALLOWANCE'
	KIND_DEDUCTION = 'DEDUCTION'

	KIND_CHOICES = [
		(KIND_ALLOWANCE, 'Allowance'),
		(KIND_DEDUCTION, 'Deduction'),
	]

	code = models.SlugField(max_length=60, unique=True)
	name = models.CharField(max_length=120)
	kind = models.CharField(max_length=20, choices=KIND_CHOICES)
	taxable = models.BooleanField(default=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['kind', 'name']
		indexes = [
			models.Index(fields=['kind']),
			models.Index(fields=['is_active']),
		]

	def __str__(self):
		return f'{self.name} ({self.kind})'


class EmployeePayItem(models.Model):
	employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pay_items')
	item_type = models.ForeignKey(PayItemType, on_delete=models.PROTECT, related_name='employee_items')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	start_date = models.DateField(null=True, blank=True)
	end_date = models.DateField(null=True, blank=True)
	is_recurring = models.BooleanField(default=True)
	is_active = models.BooleanField(default=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_pay_items')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		indexes = [
			models.Index(fields=['employee', 'is_active']),
			models.Index(fields=['item_type', 'is_active']),
		]

	def __str__(self):
		return f'{self.employee} - {self.item_type} - {self.amount}'

	def applies_to_date(self, date_value):
		if not self.is_active:
			return False
		if self.start_date and date_value < self.start_date:
			return False
		if self.end_date and date_value > self.end_date:
			return False
		return True


class Penalty(models.Model):
	STATUS_PENDING = 'PENDING'
	STATUS_CLEARED = 'CLEARED'
	STATUS_WAIVED = 'WAIVED'

	STATUS_CHOICES = [
		(STATUS_PENDING, 'Pending Clearance'),
		(STATUS_CLEARED, 'Cleared (Deduct)'),
		(STATUS_WAIVED, 'Waived'),
	]

	employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='penalties')
	department = models.ForeignKey('employees.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='penalties')
	incident_date = models.DateField(default=timezone.localdate)
	applies_to_month = models.DateField(help_text='Use first day of month')
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	reason = models.TextField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_penalties')
	created_at = models.DateTimeField(auto_now_add=True)
	cleared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='cleared_penalties')
	cleared_at = models.DateTimeField(null=True, blank=True)
	clearance_notes = models.TextField(blank=True)

	class Meta:
		ordering = ['-incident_date', '-created_at']
		indexes = [
			models.Index(fields=['status']),
			models.Index(fields=['employee', 'applies_to_month']),
		]

	def __str__(self):
		return f'Penalty {self.employee} {self.amount} ({self.get_status_display()})'


class PayrollRun(models.Model):
	month = models.DateField(help_text='Use first day of month')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payroll_runs')
	created_at = models.DateTimeField(auto_now_add=True)
	locked = models.BooleanField(default=False, help_text='When locked, this payroll run should not be recalculated.')

	class Meta:
		indexes = [models.Index(fields=['month'])]
		constraints = [
			models.UniqueConstraint(fields=['month'], name='unique_payroll_run_month'),
		]

	def __str__(self):
		return f'Payroll {self.month:%Y-%m}'


class Payslip(models.Model):
	payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
	employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payslips')
	basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	allowance_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	deduction_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	penalty_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
	tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
	net_pay = models.DecimalField(max_digits=12, decimal_places=2)
	pdf_file = models.FileField(upload_to='payslips/', blank=True, null=True)
	is_held = models.BooleanField(default=False, help_text='Held until penalty clearance is completed.')

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['payroll_run', 'employee'], name='unique_payslip_per_run'),
		]

	def __str__(self):
		return f'Payslip {self.employee} - {self.payroll_run}'


class SalaryVoucher(models.Model):
	STATUS_ON_HOLD = 'ON_HOLD'
	STATUS_CLEARED = 'CLEARED'

	STATUS_CHOICES = [
		(STATUS_ON_HOLD, 'On Hold (Penalty Clearance)'),
		(STATUS_CLEARED, 'Cleared'),
	]

	payslip = models.OneToOneField(Payslip, on_delete=models.CASCADE, related_name='salary_voucher')
	voucher_number = models.CharField(max_length=40, unique=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ON_HOLD)
	cleared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='cleared_salary_vouchers')
	cleared_at = models.DateTimeField(null=True, blank=True)
	clearance_notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		indexes = [
			models.Index(fields=['status']),
		]

	def __str__(self):
		return f'Salary Voucher {self.voucher_number} - {self.payslip.employee}'
