from django.conf import settings
from django.db import models


class Event(models.Model):
	title = models.CharField(max_length=200)
	start_date = models.DateField()
	end_date = models.DateField()
	notes = models.TextField(blank=True)
	is_public = models.BooleanField(default=True)
	is_holiday = models.BooleanField(default=False)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

	class Meta:
		ordering = ['start_date']
		indexes = [
			models.Index(fields=['start_date']),
			models.Index(fields=['is_holiday']),
		]

	def __str__(self):
		return self.title
