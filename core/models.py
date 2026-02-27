from django.core.validators import RegexValidator
from django.db import models


def inbox_attachment_upload_to(instance, filename):
	return f'inbox_attachments/{instance.email_id}/{filename}'


hex_color_validator = RegexValidator(
	regex=r'^#(?:[0-9A-Fa-f]{3}){1,2}$',
	message='Enter a valid HEX color (e.g. #2563eb).',
)


class BrandingSettings(models.Model):
	DEFAULT_APP_NAME = 'Jambas HRMS'
	DEFAULT_TAGLINE = 'Human Resource Portal'
	DEFAULT_PRIMARY_COLOR = '#2563eb'
	DEFAULT_PRIMARY_HOVER_COLOR = '#1d4ed8'
	DEFAULT_SECONDARY_COLOR = '#64748b'
	DEFAULT_ACCENT_COLOR = '#3b82f6'
	DEFAULT_SIDEBAR_COLOR = '#0f172a'
	DEFAULT_BODY_BG_COLOR = '#f1f5f9'
	DEFAULT_TEXT_MAIN_COLOR = '#1e293b'
	DEFAULT_TEXT_MUTED_COLOR = '#64748b'
	DEFAULT_TEXT_LIGHT_COLOR = '#f8fafc'
	DEFAULT_FOOTER_TEXT_COLOR = '#ffffff'
	DEFAULT_FOOTER_LINK_TEXT = 'DEVTOWN TECHNOLOGIES'
	DEFAULT_FOOTER_LINK_URL = 'https://www.devtownhosting.com'

	app_name = models.CharField(max_length=120, default='Jambas HRMS')
	tagline = models.CharField(max_length=180, blank=True, default='Human Resource Portal')
	logo = models.ImageField(upload_to='branding/', blank=True, null=True)

	company_address = models.CharField(max_length=255, blank=True)
	company_phone = models.CharField(max_length=60, blank=True)
	company_email = models.EmailField(blank=True)

	hr_name = models.CharField(max_length=120, blank=True)
	hr_title = models.CharField(max_length=120, blank=True, default='Human Resource')
	hr_signature = models.ImageField(upload_to='branding/', blank=True, null=True)

	primary_color = models.CharField(max_length=7, default=DEFAULT_PRIMARY_COLOR, validators=[hex_color_validator])
	primary_hover_color = models.CharField(max_length=7, default=DEFAULT_PRIMARY_HOVER_COLOR, validators=[hex_color_validator])
	secondary_color = models.CharField(max_length=7, default=DEFAULT_SECONDARY_COLOR, validators=[hex_color_validator])
	accent_color = models.CharField(max_length=7, default=DEFAULT_ACCENT_COLOR, validators=[hex_color_validator])
	sidebar_color = models.CharField(max_length=7, default=DEFAULT_SIDEBAR_COLOR, validators=[hex_color_validator])
	body_bg_color = models.CharField(max_length=7, default=DEFAULT_BODY_BG_COLOR, validators=[hex_color_validator])
	text_main_color = models.CharField(max_length=7, default=DEFAULT_TEXT_MAIN_COLOR, validators=[hex_color_validator])
	text_muted_color = models.CharField(max_length=7, default=DEFAULT_TEXT_MUTED_COLOR, validators=[hex_color_validator])
	text_light_color = models.CharField(max_length=7, default=DEFAULT_TEXT_LIGHT_COLOR, validators=[hex_color_validator])

	login_show_branding = models.BooleanField(default=True)
	login_show_logo = models.BooleanField(default=False)

	footer_enabled = models.BooleanField(default=True)
	footer_left_text = models.CharField(max_length=220, blank=True)
	footer_right_text = models.CharField(max_length=220, blank=True, default='System developed by')
	footer_link_text = models.CharField(max_length=120, blank=True, default=DEFAULT_FOOTER_LINK_TEXT)
	footer_link_url = models.URLField(blank=True, default=DEFAULT_FOOTER_LINK_URL)
	footer_bg_color = models.CharField(max_length=7, default=DEFAULT_PRIMARY_COLOR, validators=[hex_color_validator])
	footer_text_color = models.CharField(max_length=7, default=DEFAULT_FOOTER_TEXT_COLOR, validators=[hex_color_validator])

	public_access_code_enabled = models.BooleanField(default=False)
	public_access_code_hash = models.CharField(max_length=255, blank=True)
	public_access_code_version = models.PositiveIntegerField(default=1)

	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Branding Settings'
		verbose_name_plural = 'Branding Settings'

	def save(self, *args, **kwargs):
		self.pk = 1
		super().save(*args, **kwargs)

	@classmethod
	def get_solo(cls):
		obj, _ = cls.objects.get_or_create(pk=1)
		return obj

	def __str__(self):
		return self.app_name

	def reset_to_defaults(self):
		self.app_name = self.DEFAULT_APP_NAME
		self.tagline = self.DEFAULT_TAGLINE
		self.primary_color = self.DEFAULT_PRIMARY_COLOR
		self.primary_hover_color = self.DEFAULT_PRIMARY_HOVER_COLOR
		self.secondary_color = self.DEFAULT_SECONDARY_COLOR
		self.accent_color = self.DEFAULT_ACCENT_COLOR
		self.sidebar_color = self.DEFAULT_SIDEBAR_COLOR
		self.body_bg_color = self.DEFAULT_BODY_BG_COLOR
		self.text_main_color = self.DEFAULT_TEXT_MAIN_COLOR
		self.text_muted_color = self.DEFAULT_TEXT_MUTED_COLOR
		self.text_light_color = self.DEFAULT_TEXT_LIGHT_COLOR
		self.logo = None
		self.company_address = ''
		self.company_phone = ''
		self.company_email = ''
		self.hr_name = ''
		self.hr_title = 'Human Resource'
		self.hr_signature = None
		self.login_show_branding = True
		self.login_show_logo = False
		self.footer_enabled = True
		self.footer_left_text = ''
		self.footer_right_text = 'System developed by'
		self.footer_link_text = self.DEFAULT_FOOTER_LINK_TEXT
		self.footer_link_url = self.DEFAULT_FOOTER_LINK_URL
		self.footer_bg_color = self.DEFAULT_PRIMARY_COLOR
		self.footer_text_color = self.DEFAULT_FOOTER_TEXT_COLOR


class InboxState(models.Model):
	"""Tracks IMAP sync progress per mailbox."""
	mailbox = models.CharField(max_length=255, unique=True, default='INBOX')
	uidvalidity = models.PositiveBigIntegerField(default=0)
	last_uid = models.PositiveBigIntegerField(default=0)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Inbox State'
		verbose_name_plural = 'Inbox States'

	def __str__(self):
		return f'{self.mailbox} (last_uid={self.last_uid})'


class InboundEmail(models.Model):
	mailbox = models.CharField(max_length=255, default='INBOX')
	uid = models.PositiveBigIntegerField()

	message_id = models.CharField(max_length=255, blank=True, db_index=True)
	in_reply_to = models.CharField(max_length=255, blank=True)
	references = models.TextField(blank=True)

	subject = models.CharField(max_length=255, blank=True)
	from_name = models.CharField(max_length=255, blank=True)
	from_email = models.CharField(max_length=255, blank=True)
	to = models.TextField(blank=True)
	cc = models.TextField(blank=True)

	sent_at = models.DateTimeField(null=True, blank=True)
	body_text = models.TextField(blank=True)

	fetched_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = 'Inbound Email'
		verbose_name_plural = 'Inbound Emails'
		constraints = [
			models.UniqueConstraint(fields=['mailbox', 'uid'], name='unique_inbound_email_mailbox_uid'),
		]
		indexes = [
			models.Index(fields=['mailbox', '-uid'], name='inbound_mailbox_uid_idx'),
		]

	def __str__(self):
		return f'{self.from_email} - {self.subject}'

	@property
	def snippet(self):
		text = (self.body_text or '').strip().replace('\r', ' ').replace('\n', ' ')
		return (text[:120] + '…') if len(text) > 120 else text


class InboundEmailAttachment(models.Model):
	email = models.ForeignKey(InboundEmail, on_delete=models.CASCADE, related_name='attachments')
	filename = models.CharField(max_length=255, blank=True)
	content_type = models.CharField(max_length=120, blank=True)
	size = models.PositiveBigIntegerField(default=0)
	file = models.FileField(upload_to=inbox_attachment_upload_to)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = 'Inbound Email Attachment'
		verbose_name_plural = 'Inbound Email Attachments'

	def __str__(self):
		return self.filename or 'attachment'
