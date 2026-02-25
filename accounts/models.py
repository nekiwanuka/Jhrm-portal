from django.contrib.auth.models import AbstractUser
from django.db import models


class BusinessRole(models.Model):
	code = models.SlugField(max_length=60, unique=True)
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True)

	department_scope = models.ForeignKey(
		'employees.Department',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		help_text='Optional. If set, role is scoped to this department.',
	)

	approval_authority_level = models.PositiveSmallIntegerField(default=0)
	financial_authorization_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['name']
		indexes = [
			models.Index(fields=['code']),
			models.Index(fields=['is_active']),
		]

	def __str__(self):
		return self.name


class User(AbstractUser):
	ROLE_SUPER_ADMIN = 'SUPER_ADMIN'
	ROLE_HR_MANAGER = 'HR_MANAGER'
	ROLE_SUPERVISOR = 'SUPERVISOR'
	ROLE_STAFF = 'STAFF'

	ROLE_CHOICES = [
		(ROLE_SUPER_ADMIN, 'Super Admin'),
		(ROLE_HR_MANAGER, 'HR Manager'),
		(ROLE_SUPERVISOR, 'Supervisor'),
		(ROLE_STAFF, 'Staff'),
	]

	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)
	phone_number = models.CharField(max_length=30, blank=True)

	class Meta:
		indexes = [
			models.Index(fields=['role']),
			models.Index(fields=['email']),
		]

	def __str__(self):
		return f'{self.get_full_name() or self.username} ({self.role})'
