from django.conf import settings
from django.db import models


class Notice(models.Model):
	title = models.CharField(max_length=200)
	content = models.TextField()
	is_public = models.BooleanField(default=True)
	expiry_date = models.DateField(null=True, blank=True)
	created_by_name = models.CharField(max_length=160, blank=True)
	created_by_phone = models.CharField(max_length=30, blank=True)
	created_by_department = models.CharField(max_length=120, blank=True)
	created_by_position = models.CharField(max_length=120, blank=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='notices_created')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['is_public']),
			models.Index(fields=['expiry_date']),
		]

	def __str__(self):
		return self.title


class NoticeComment(models.Model):
	notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='comments')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='notice_comments')
	comment = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']
		indexes = [
			models.Index(fields=['notice']),
			models.Index(fields=['created_at']),
		]

	def __str__(self):
		return f'Comment on {self.notice_id} by {self.user_id}'
