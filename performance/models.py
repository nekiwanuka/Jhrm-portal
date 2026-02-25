from django.conf import settings
from django.db import models


class KPI(models.Model):
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True)
	weight = models.PositiveSmallIntegerField(default=10)

	def __str__(self):
		return self.name


class PerformanceReview(models.Model):
	employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='performance_reviews')
	reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reviews_made')
	period_start = models.DateField()
	period_end = models.DateField()
	kpi_score = models.DecimalField(max_digits=5, decimal_places=2)
	comments = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		indexes = [
			models.Index(fields=['period_start', 'period_end']),
			models.Index(fields=['kpi_score']),
		]

	def __str__(self):
		return f'{self.employee} review ({self.period_start} - {self.period_end})'
