from __future__ import annotations

from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render_user_manual_pdf(*, user, branding, is_hr_admin: bool, is_supervisor_plus: bool) -> HttpResponse:
	"""Generate a role-aware User Manual PDF using ReportLab (no cairo/meson deps)."""
	role_label = 'Staff'
	if is_hr_admin:
		role_label = 'HR Admin'
	elif is_supervisor_plus:
		role_label = 'Supervisor'

	buffer = BytesIO()
	doc = SimpleDocTemplate(
		buffer,
		pagesize=A4,
		topMargin=36,
		bottomMargin=36,
		leftMargin=40,
		rightMargin=40,
		title=f"{getattr(branding, 'app_name', 'HRMS')} User Manual",
	)

	styles = getSampleStyleSheet()
	styles.add(ParagraphStyle(name='H1', parent=styles['Heading1'], fontSize=18, spaceAfter=10))
	styles.add(ParagraphStyle(name='H2', parent=styles['Heading2'], fontSize=13, spaceBefore=14, spaceAfter=6))
	styles.add(ParagraphStyle(name='Body', parent=styles['BodyText'], fontSize=10.5, leading=14))
	styles.add(ParagraphStyle(name='Muted', parent=styles['BodyText'], fontSize=9.5, textColor=colors.HexColor('#4b5563')))
	styles.add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontSize=9, textColor=colors.HexColor('#6b7280')))

	app_name = getattr(branding, 'app_name', None) or 'HRMS'
	full_name = (getattr(user, 'get_full_name', lambda: '')() or '').strip() or getattr(user, 'username', 'User')
	date_str = timezone.localdate().strftime('%Y-%m-%d')

	story: list = []
	story.append(Paragraph(f"{app_name} — User Manual", styles['H1']))
	story.append(Paragraph("A practical guide with examples, tailored to your role permissions.", styles['Muted']))
	story.append(Spacer(1, 12))

	meta = Table(
		[
			['Role:', role_label],
			['Generated for:', full_name],
			['Date:', date_str],
		],
		colWidths=[95, 380],
	)
	meta.setStyle(
		TableStyle(
			[
				('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
				('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#e5e7eb')),
				('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
				('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
				('FONTSIZE', (0, 0), (-1, -1), 10),
				('PADDING', (0, 0), (-1, -1), 6),
			]
		)
	)
	story.append(meta)
	story.append(Spacer(1, 14))

	def h2(text: str):
		story.append(Paragraph(text, styles['H2']))

	def p(text: str):
		story.append(Paragraph(text, styles['Body']))
		story.append(Spacer(1, 6))

	def bullet(items: list[str]):
		for item in items:
			story.append(Paragraph(f"• {item}", styles['Body']))
		story.append(Spacer(1, 6))

	def example(text: str):
		t = Table([[Paragraph(f"<b>Example:</b> {text}", styles['Body'])]], colWidths=[475])
		t.setStyle(
			TableStyle(
				[
					('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fbff')),
					('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#dbeafe')),
					('LEFTPADDING', (0, 0), (-1, -1), 8),
					('RIGHTPADDING', (0, 0), (-1, -1), 8),
					('TOPPADDING', (0, 0), (-1, -1), 8),
					('BOTTOMPADDING', (0, 0), (-1, -1), 8),
				]
			)
		)
		story.append(t)
		story.append(Spacer(1, 8))

	# 1. Getting Started
	h2('1. Getting Started')
	p('<b>Login</b>')
	bullet([
		'Open the system URL in your browser.',
		'Enter your email address and password.',
		'Select “Sign in”.',
	])
	story.append(Paragraph("If you forgot your password, contact your HR Admin.", styles['Small']))
	story.append(Spacer(1, 10))

	p('<b>Navigation</b>')
	bullet([
		'The sidebar contains the main modules (Dashboard, Noticeboard, Tasks, Calendar, etc.).',
		'Some menu items appear only if your role has permission.',
	])

	# 2. Common Modules
	h2('2. Common Modules (All Users)')
	p('<b>Dashboard</b> — shows quick counts and shortcuts for your daily work.')
	p('<b>Noticeboard</b> — view organization announcements and updates.')
	example('A policy update notice appears with a date and details; read and share with your team.')
	p('<b>Tasks</b> — view tasks assigned to you and update status as you work.')
	example('A task called “Submit weekly report” moves from To Do → In Progress → Done.')
	p('<b>Calendar</b> — review upcoming events and important dates.')

	# 3. Leave
	h2('3. Leave Management')
	p('<b>Request Leave</b>')
	bullet([
		'Open Leave from the sidebar.',
		'Select Create/Request Leave.',
		'Fill leave type, dates, and reason, then submit.',
	])
	example('Request annual leave for 3 days. The request becomes Pending until approved.')

	if is_supervisor_plus:
		h2('4. Supervisor Tools')
		p('<b>Approve / Reject Leave</b>')
		bullet([
			'Open Leave and navigate to approvals (if available).',
			'Review request details, then approve or reject with a clear comment.',
		])
		example('Approve leave and add: “Approved. Ensure handover by Friday.”')

		p('<b>Send Email</b> (Supervisor+ tool)')
		bullet([
			'Open Send Email from the sidebar.',
			'Enter recipients (comma-separated or one per line), subject, and message.',
			'Select Send.',
		])
		story.append(Paragraph('Emails are sent using the SMTP settings configured by the administrator.', styles['Small']))
		story.append(Spacer(1, 8))

	if is_hr_admin:
		h2('5. HR Admin & System Administration')
		p('<b>Employees</b> — create/update employee profiles and manage documents where permitted.')
		p('<b>Attendance</b> — review attendance records and correct mistakes per policy.')
		p('<b>Reports</b> — review weekly reports and follow up on missing submissions.')
		p('<b>Theme Settings</b> — update branding, colors, footer, and login branding/logo toggles.')
		p('<b>Public Access Code</b> — enable and set access-code protection for public pages (if used).')

	# 6. Roles
	h2('6. Roles & Permissions Summary')
	roles_table = Table(
		[
			['Role', 'Typical Access'],
			['Staff', 'Personal dashboard, tasks, notices, leave requests, weekly reports (as assigned).'],
			['Supervisor', 'Everything staff can do + approvals and team oversight tools (where enabled).'],
			['HR Manager / Super Admin', 'Full HR administration, employee management, settings, and oversight dashboards.'],
		],
		colWidths=[150, 325],
	)
	roles_table.setStyle(
		TableStyle(
			[
				('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f9fafb')),
				('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#e5e7eb')),
				('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
				('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
				('VALIGN', (0, 0), (-1, -1), 'TOP'),
				('PADDING', (0, 0), (-1, -1), 6),
			]
		)
	)
	story.append(roles_table)
	story.append(Spacer(1, 14))

	story.append(Paragraph(f"Generated by {app_name}.", styles['Small']))

	doc.build(story)
	pdf_bytes = buffer.getvalue()
	buffer.close()

	filename = f"user-manual-{role_label.lower().replace(' ', '-')}.pdf"
	response = HttpResponse(pdf_bytes, content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="{filename}"'
	return response
