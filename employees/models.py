from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Department(models.Model):
	TYPE_OPERATIONAL = 'OPERATIONAL'
	TYPE_ADMINISTRATIVE = 'ADMINISTRATIVE'
	TYPE_EXECUTIVE = 'EXECUTIVE'

	TYPE_CHOICES = [
		(TYPE_OPERATIONAL, 'Operational'),
		(TYPE_ADMINISTRATIVE, 'Administrative'),
		(TYPE_EXECUTIVE, 'Executive'),
	]

	name = models.CharField(max_length=120, unique=True)
	department_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_OPERATIONAL)
	description = models.TextField(blank=True)
	parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
	cost_center_code = models.CharField(max_length=40, blank=True)
	budget_allocation = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	head = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['name']
		indexes = [
			models.Index(fields=['is_active']),
			models.Index(fields=['department_type']),
		]

	def __str__(self):
		return self.name


class Position(models.Model):
	title = models.CharField(max_length=120)
	department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['title', 'department'], name='unique_position_per_department'),
		]

	def __str__(self):
		return f'{self.title} - {self.department.name}'


class EmployeeProfile(models.Model):
	STATUS_ACTIVE = 'ACTIVE'
	STATUS_ON_LEAVE = 'ON_LEAVE'
	STATUS_RESIGNED = 'RESIGNED'
	STATUS_TERMINATED = 'TERMINATED'

	EMPLOYMENT_STATUS_CHOICES = [
		(STATUS_ACTIVE, 'Active'),
		(STATUS_ON_LEAVE, 'On Leave'),
		(STATUS_RESIGNED, 'Resigned'),
		(STATUS_TERMINATED, 'Terminated'),
	]

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
	employee_id = models.CharField(max_length=20, unique=True)
	photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
	department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
	position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)

	# Personal information
	national_id = models.CharField(max_length=30, blank=True)
	passport_number = models.CharField(max_length=30, blank=True)
	tin = models.CharField(max_length=30, blank=True)
	nssf_number = models.CharField(max_length=30, blank=True)
	date_of_birth = models.DateField(null=True, blank=True)
	gender = models.CharField(max_length=20, blank=True)
	marital_status = models.CharField(max_length=30, blank=True)
	emergency_contact_name = models.CharField(max_length=120, blank=True)
	emergency_contact_phone = models.CharField(max_length=30, blank=True)

	# Employment information
	EMPLOYMENT_FULL_TIME = 'FULL_TIME'
	EMPLOYMENT_CONTRACT = 'CONTRACT'
	EMPLOYMENT_TEMPORARY = 'TEMPORARY'
	EMPLOYMENT_INTERN = 'INTERN'
	EMPLOYMENT_CONSULTANT = 'CONSULTANT'

	EMPLOYMENT_TYPE_CHOICES = [
		(EMPLOYMENT_FULL_TIME, 'Permanent'),
		(EMPLOYMENT_CONTRACT, 'Contract'),
		(EMPLOYMENT_TEMPORARY, 'Temporary'),
		(EMPLOYMENT_INTERN, 'Intern'),
		(EMPLOYMENT_CONSULTANT, 'Consultant'),
	]

	employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default=EMPLOYMENT_FULL_TIME)
	date_hired = models.DateField()
	probation_end_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default=STATUS_ACTIVE)

	# Bank details
	bank_name = models.CharField(max_length=120, blank=True)
	bank_account_number = models.CharField(max_length=60, blank=True)
	bank_branch = models.CharField(max_length=120, blank=True)

	class Meta:
		indexes = [
			models.Index(fields=['employee_id']),
			models.Index(fields=['status']),
			models.Index(fields=['employment_type']),
		]

	def __str__(self):
		return f'{self.user.get_full_name() or self.user.username} ({self.employee_id})'


class EmployeeDepartmentRole(models.Model):
	employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='department_roles')
	department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employee_roles')
	role = models.ForeignKey('accounts.BusinessRole', on_delete=models.PROTECT, related_name='employee_assignments')
	reporting_manager = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='direct_reports',
	)
	effective_start_date = models.DateField(null=True, blank=True)
	effective_end_date = models.DateField(null=True, blank=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		indexes = [
			models.Index(fields=['is_active']),
			models.Index(fields=['department']),
			models.Index(fields=['role']),
		]
		constraints = [
			models.UniqueConstraint(
				fields=['employee', 'department', 'role'],
				name='unique_employee_department_role',
			),
		]

	def __str__(self):
		return f'{self.employee} - {self.department} - {self.role}'

	def clean(self):
		if self.role_id and self.department_id:
			if self.role.department_scope_id and self.role.department_scope_id != self.department_id:
				raise ValidationError('Role department scope must match the selected department.')


class EmployeeDocument(models.Model):
	DOC_CV = 'CV'
	DOC_CERTIFICATE = 'CERTIFICATE'
	DOC_CONTRACT = 'CONTRACT'
	DOC_NDA = 'NDA'
	DOC_PERFORMANCE = 'PERFORMANCE'
	DOC_OTHER = 'OTHER'

	DOC_TYPE_CHOICES = [
		(DOC_CV, 'CV'),
		(DOC_CERTIFICATE, 'Certificate'),
		(DOC_CONTRACT, 'Signed Contract'),
		(DOC_NDA, 'NDA'),
		(DOC_PERFORMANCE, 'Performance Agreement'),
		(DOC_OTHER, 'Other'),
	]

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_documents')
	document_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default=DOC_OTHER)
	file = models.FileField(upload_to='employee_documents/')
	description = models.CharField(max_length=255, blank=True)
	uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-uploaded_at']
		indexes = [
			models.Index(fields=['user']),
			models.Index(fields=['document_type']),
		]

	def __str__(self):
		return f'{self.user.username} - {self.document_type}'
