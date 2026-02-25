from django.conf import settings
from django.db import models


class AttendanceRecord(models.Model):
	employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_records')
	date = models.DateField()
	check_in = models.DateTimeField()
	check_out = models.DateTimeField(null=True, blank=True)
	is_late = models.BooleanField(default=False)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['employee', 'date'], name='unique_attendance_per_day'),
		]
		indexes = [
			models.Index(fields=['date']),
			models.Index(fields=['is_late']),
		]

	def __str__(self):
		return f'{self.employee} - {self.date}'
