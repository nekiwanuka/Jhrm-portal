from django.core.validators import RegexValidator
from django.db import models


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
