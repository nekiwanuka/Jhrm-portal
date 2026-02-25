from django.conf import settings
from django.db import models
from django.utils import timezone


class Task(models.Model):
	VISIBILITY_ALL = 'ALL'
	VISIBILITY_USER = 'USER'

	VISIBILITY_CHOICES = [
		(VISIBILITY_ALL, 'Everyone'),
		(VISIBILITY_USER, 'One person'),
	]

	STATUS_TODO = 'TODO'
	STATUS_IN_PROGRESS = 'IN_PROGRESS'
	STATUS_DONE = 'DONE'
	STATUS_REDO = 'REDO'

	STATUS_CHOICES = [
		(STATUS_TODO, 'To Do'),
		(STATUS_IN_PROGRESS, 'In Progress'),
		(STATUS_DONE, 'Done'),
		(STATUS_REDO, 'Re-Do'),
	]

	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default=VISIBILITY_ALL)
	visible_to = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='personal_tasks',
		help_text='If set to "One person", only that user (and admins) can see this task.',
	)
	assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='tasks_created')
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
	position = models.PositiveIntegerField(default=0, db_index=True)
	progress = models.PositiveSmallIntegerField(default=0)
	deadline = models.DateField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['status', 'position', 'deadline', '-created_at']
		indexes = [
			models.Index(fields=['status']),
			models.Index(fields=['status', 'position']),
			models.Index(fields=['visibility']),
			models.Index(fields=['visibility', 'visible_to']),
			models.Index(fields=['deadline']),
		]

	def __str__(self):
		return self.title

	@property
	def is_overdue(self):
		if not self.deadline:
			return False
		return self.deadline < timezone.localdate() and self.status != self.STATUS_DONE

	@property
	def is_due_soon(self):
		if not self.deadline:
			return False
		today = timezone.localdate()
		if self.status == self.STATUS_DONE:
			return False
		delta_days = (self.deadline - today).days
		return 0 <= delta_days <= 3
