from django.conf import settings
from django.db import models


class AuditLog(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	action = models.CharField(max_length=100)
	path = models.CharField(max_length=255)
	method = models.CharField(max_length=10)
	status_code = models.PositiveSmallIntegerField(default=200)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['created_at']),
			models.Index(fields=['action']),
		]

	def __str__(self):
		return f'{self.action} - {self.path}'


class Notification(models.Model):
	LEVEL_INFO = 'INFO'
	LEVEL_WARNING = 'WARNING'
	LEVEL_DANGER = 'DANGER'

	LEVEL_CHOICES = [
		(LEVEL_INFO, 'Info'),
		(LEVEL_WARNING, 'Warning'),
		(LEVEL_DANGER, 'Danger'),
	]

	recipient = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='notifications',
	)
	actor = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='notifications_sent',
	)
	message = models.CharField(max_length=255)
	path = models.CharField(max_length=255, blank=True)
	level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default=LEVEL_INFO)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['recipient', 'is_read', 'created_at']),
			models.Index(fields=['created_at']),
		]

	def __str__(self):
		return self.message
