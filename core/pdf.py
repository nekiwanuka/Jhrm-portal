from __future__ import annotations

from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render_user_manual_pdf(
	*,
	user,
	branding,
	is_hr_admin: bool,
	is_supervisor_plus: bool,
	generated_for_name: str | None = None,
	manual_role_label: str | None = None,
) -> HttpResponse:
	"""Generate a role-aware User Manual PDF using ReportLab (no cairo/meson deps)."""
	role_label = manual_role_label or 'Staff'
	if not manual_role_label:
		if is_hr_admin:
			role_label = 'HR/Admin'
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
	styles.add(ParagraphStyle(name='H2', parent=styles['Heading2'], fontSize=13.5, spaceBefore=14, spaceAfter=6))
	styles.add(ParagraphStyle(name='H3', parent=styles['Heading3'], fontSize=11.5, spaceBefore=10, spaceAfter=4))
	styles.add(ParagraphStyle(name='Body', parent=styles['BodyText'], fontSize=10.5, leading=14))
	styles.add(ParagraphStyle(name='Muted', parent=styles['BodyText'], fontSize=9.5, textColor=colors.HexColor('#4b5563')))
	styles.add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontSize=9, textColor=colors.HexColor('#6b7280')))

	app_name = getattr(branding, 'app_name', None) or 'HRMS'
	full_name = generated_for_name or ((getattr(user, 'get_full_name', lambda: '')() or '').strip() or getattr(user, 'username', 'User'))
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

	def h3(text: str):
		story.append(Paragraph(text, styles['H3']))

	def p(text: str):
		story.append(Paragraph(text, styles['Body']))
		story.append(Spacer(1, 6))

	def bullet(items: list[str]):
		for item in items:
			story.append(Paragraph(f"• {item}", styles['Body']))
		story.append(Spacer(1, 6))

	def tip(text: str):
		story.append(Paragraph(f"<b>Tip:</b> {text}", styles['Muted']))
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

	def toc_line(text: str):
		story.append(Paragraph(f"• {text}", styles['Body']))

	# Table of contents (role-aware)
	h2('Contents')
	toc_line('1. Accounts & Security')
	toc_line('2. Dashboard')
	toc_line('3. My Documents')
	toc_line('4. Weekly Reports')
	toc_line('5. Leave Management')
	toc_line('6. Tasks')
	if is_supervisor_plus:
		toc_line('7. Tools & Communication (Supervisor+)')
	toc_line('8. Noticeboard')
	toc_line('9. Calendar')
	if is_supervisor_plus:
		toc_line('10. Attendance (Supervisor+)')
		toc_line('11. Performance Reviews (Supervisor+)')
		toc_line('12. Employees (Supervisor+)')
		toc_line('13. Reports & CSV Export (Supervisor+)')
	if is_hr_admin:
		toc_line('14. Payroll (HR/Admin)')
		toc_line('15. Administration Settings (HR/Admin)')
		toc_line('16. Audit Logs & Notifications (HR/Admin)')
	toc_line('17. Troubleshooting & FAQ')
	toc_line('18. Roles & Permissions Summary')
	story.append(Spacer(1, 10))

	# 1. Accounts & Security
	h2('1. Accounts & Security')
	h3('1.1 Login')
	bullet([
		'Open the system URL in your browser.',
		'Enter your email address and password.',
		'Select “Sign in”.',
	])
	tip('If your account is suspended/disabled, contact HR Admin to restore access.')

	h3('1.2 Logout')
	bullet([
		'Use the user menu/logout option in the header (when available).',
		'Always log out when using a shared computer.',
	])

	h3('1.3 Password & Access')
	p('If you forgot your password, follow your organization’s recovery process (typically handled by HR Admin).')

	# 2. Dashboard
	h2('2. Dashboard')
	bullet([
		'Dashboard shows KPIs, shortcuts, and activity depending on your role.',
		'Staff users may see a staff dashboard focused on personal items (documents, tasks, leave, weekly reports).',
	])
	example('If you are Staff: use the dashboard counters to quickly find pending leave requests and tasks assigned to you.')

	# 3. My Documents
	h2('3. My Documents')
	h3('3.1 View your documents')
	bullet([
		'Open “My Documents” from the sidebar.',
		'Use the list to review files you previously uploaded.',
	])

	h3('3.2 Upload a document')
	bullet([
		'Open “My Documents” → Upload.',
		'Choose a file (PDF, image, or allowed document format).',
		'Save to upload it to your profile.',
	])
	example('Upload a scanned National ID as “ID Document” so HR can confirm your identity.')

	h3('3.3 Delete a document')
	bullet([
		'Open “My Documents”.',
		'Select Delete on the target file.',
		'Confirm deletion.',
	])
	tip('Only upload official documents. Avoid sharing passwords or confidential secrets in uploads.')

	# 4. Weekly Reports
	h2('4. Weekly Reports')
	h3('4.1 Submit a weekly report')
	bullet([
		'Open “Weekly Reports” from the sidebar.',
		'Select “Submit”.',
		'Choose the Week Start date and fill in achievements, challenges, and next week plan.',
		'Submit the report.',
	])
	example('Submit Week Start: 2026-02-24 with highlights and planned tasks for the next week.')
	tip('Supervisors and HR can use weekly reports for follow-up and performance reviews. Keep reports factual and measurable (numbers, dates, deliverables).')

	h3('4.2 View weekly reports')
	bullet([
		'Staff: sees only their own submissions.',
		'Supervisor+: can see department/team submissions (based on department).',
		'HR Admin: can see all weekly reports across the organization.',
	])
	tip('If you submit multiple times for the same week, the system records submission numbers (e.g., #1, #2).')

	# 5. Leave
	h2('5. Leave Management')
	h3('5.0 Leave status and entitlements')
	bullet([
		'Leave requests move through statuses: Pending → Approved / Rejected.',
		'For staff users, the Leave list may show an “Entitlements” summary for the current year (max days, used days, remaining days) per leave type.',
		'Entitlements are calculated from Approved leave requests within the current year.',
	])
	example('If Annual Leave max is 21 days and you already have 5 approved days this year, remaining days show as 16.')

	h3('5.1 Request leave (Staff)')
	bullet([
		'Open “Leave”.',
		'Select “Request / Create”.',
		'Choose leave type, start and end dates, and add a reason.',
		'Submit for approval.',
	])
	example('Request Annual Leave: 2026-03-03 to 2026-03-05, reason “Family commitment”.')
	tip('Submit leave early. Your approver may need time to plan staffing and handover.')

	if is_supervisor_plus:
		h3('5.2 Approve / reject leave (Supervisor+)')
		bullet([
			'Open “Leave” and review pending requests.',
			'Open a request and confirm dates, leave type, and employee details.',
			'Approve or reject with a clear comment.',
		])
		example('Approve leave and comment: “Approved. Ensure handover is completed before departure.”')
		bullet([
			'Changing a decision back to Pending clears the approver and decision timestamp (used when re-reviewing a request).',
			'Only approve if the request fits leave entitlements/policy and coverage is arranged.',
		])

	if is_hr_admin:
		h3('5.3 Leave offer letter (HR/Admin)')
		bullet([
			'From a leave request, open “Letter”.',
			'Download/print the generated leave offer letter.',
		])
		tip('Use the offer letter for formal documentation where required (e.g., internal file, employee confirmation).')

		h3('5.4 Manage leave types (HR Admin)')
		bullet([
			'Open Leave → Types.',
			'Create/edit leave types (e.g., Annual, Sick).',
			'Set maximum days per year and activate/deactivate leave types as policy changes.',
		])
		example('Create “Sick Leave” with max days per year set to 14.')

	# 6. Tasks
	h2('6. Tasks')
	h3('6.1 Task board')
	bullet([
		'Task board groups items by status: To Do, In Progress, Done, Redo.',
		'You can drag tasks on the board only when logged in.',
		'Tasks visibility may be: everyone, or limited to a specific user/assignee.',
	])
	example('Move “Submit weekly report” from To Do to Done after submission.')
	bullet([
		'If you cannot move a task, it may be because you are not logged in or the task is not visible/assigned to you.',
		'Use consistent status updates so supervisors can track delivery (avoid leaving work in “In Progress” for long without notes).',
	])

	if is_supervisor_plus:
		h3('6.2 Create and manage tasks (Supervisor+)')
		bullet([
			'Open Tasks → Create.',
			'Set title, deadline, status, and visibility (Everyone vs targeted users).',
			'If targeting: select the assignee(s) who should see the task.',
			'Edit tasks when details change; delete tasks that are no longer needed.',
		])
		example('Create a task visible only to one staff member: “Update employee file”, deadline Friday.')
		bullet([
			'Use “Redo” for tasks that failed review and need correction (add a short reason so the assignee knows what to fix).',
		])
	else:
		tip('Staff users typically cannot create/edit tasks; they work on tasks assigned/visible to them.')

	# 7. Tools (Supervisor+)
	if is_supervisor_plus:
		h2('7. Tools & Communication (Supervisor+)')
		h3('7.1 Send Email')
		bullet([
			'Open Tools → Send Email from the sidebar.',
			'Add recipients (one per line or comma-separated).',
			'Enter a clear subject and your message, then send.',
		])
		example('Send a reminder to all department staff: “Weekly report due by Friday 5pm.”')
		tip('Emails are sent using the organization SMTP settings configured on the server. If sending fails, notify HR/Admin.')

	# 8. Noticeboard
	h2('8. Noticeboard')
	h3('8.1 View notices')
	bullet([
		'Open “Noticeboard” to see public notices (including those with expiry dates).',
		'Open a notice to view full details.',
	])
	example('Read a notice titled “Public Holiday Notice” and share key dates with your team.')
	bullet([
		'Expired notices may be hidden automatically based on their expiry date.',
		'Some notices may be visible publicly; treat announcements as official communication.',
	])
	tip('If comments are enabled on a notice, you must be logged in to post a comment.')

	if is_hr_admin:
		h3('8.2 Create / edit / delete notices (HR/Admin)')
		bullet([
			'Open Noticeboard → Create.',
			'Fill notice title, message, and optional expiry date, then save.',
			'Edit or delete outdated notices.',
		])
		example('Create a notice that expires after 7 days so old notices are automatically hidden.')

	# 9. Calendar
	h2('9. Calendar')
	h3('9.1 View calendar')
	bullet([
		'Calendar shows public events for the organization.',
		'Use it to plan around upcoming events and deadlines.',
	])
	example('Check the calendar before approving leave to confirm major events and ensure staffing coverage.')

	if is_supervisor_plus:
		h3('9.2 Manage events (Supervisor+)')
		bullet([
			'Open Calendar → Create event.',
			'Provide event name, start/end dates, and visibility as configured.',
			'Edit or delete events when plans change.',
		])
		example('Add an event: “Quarterly Review Meeting”, next Monday, marked as public.')

	if is_supervisor_plus:
		# 9. Attendance
		h2('10. Attendance (Supervisor+)')
		bullet([
			'Open Attendance to view recorded entries for staff.',
			'Use Create to record a new attendance record when needed (e.g., missed entry, manual record policy).',
		])
		example('Create attendance for a staff member who reported on-site for an event.')
		tip('Only create/edit attendance according to company policy. Attendance records can affect payroll and performance reviews.')

		# 10. Performance
		h2('11. Performance Reviews (Supervisor+)')
		bullet([
			'Open Performance to view reviews.',
			'Use Create to add a performance review; the current user is recorded as the reviewer.',
		])
		example('Create a review noting achievements, improvement areas, and agreed next steps.')
		bullet([
			'Write reviews using evidence: tasks delivered, weekly report highlights, attendance patterns, and measurable outcomes.',
			'Capture action items with deadlines (training, mentoring, targets).',
		])

		# 11. Employees
		h2('12. Employees (Supervisor+)')
		h3('12.1 View employees')
		bullet([
			'Open Employees to view employee profiles.',
			'HR Admin sees all employees; Supervisors may see employees in their department.',
			'Use Preview to view a full employee profile.',
		])
		example('Preview an employee profile to confirm department and position details.')
		bullet([
			'Use employee preview when approving leave, assigning tasks, or preparing performance reviews.',
		])

		if is_hr_admin:
			h3('12.2 Create / edit employees (HR/Admin)')
			bullet([
				'Employees → Create: onboard a new employee (creates a user account and profile).',
				'Employees → Edit: update employee profile details.',
			])
			example('Onboard a new staff member: create the user login + profile, assign the correct role (e.g., STAFF) and department, then confirm they can sign in.')
			bullet([
				'After onboarding, confirm the employee profile includes required HR fields (employment info, contacts, and any organization-specific fields).',
			])

			h3('12.3 Suspend / restore user access (HR/Admin)')
			bullet([
				'On the employee list, use “Toggle access” for a user.',
				'Suspended users cannot log in until access is restored.',
			])
			tip('Suspension permissions are enforced: HR Manager can suspend most users; Super Admin/superuser can suspend anyone except a superuser account.')

			h3('12.4 Manage employee documents (HR/Admin)')
			bullet([
				'Open an employee → Documents to view files uploaded for that employee.',
				'Upload additional documents or delete incorrect uploads.',
			])
			example('Upload a signed contract letter to the employee’s document list.')
			bullet([
				'Use employee documents for HR-managed files (contracts, warning letters, certifications).',
				'Use “My Documents” for employee self-service uploads (IDs, certificates, etc.).',
			])

			h3('12.5 Departments, Positions, and Assignments (HR/Admin)')
			bullet([
				'Departments: create/edit/delete departments.',
				'Positions: create/edit/delete positions (linked to departments).',
				'Assignments: manage department roles (Supervisor/HR Manager/Super Admin) and reporting manager assignments.',
			])
			tip('Department roles can grant permissions (Supervisor+ / HR/Admin). Assign carefully and deactivate roles when staff change departments.')

		# 12. Reports
		h2('13. Reports & CSV Export (Supervisor+)')
		h3('13.1 Weekly reports oversight')
		bullet([
			'Use Weekly Reports to follow up on missing reports and to support performance conversations.',
			'HR/Admin can review submissions across all departments; Supervisors focus on their department/team.',
		])

		h3('13.2 Report requests')
		bullet([
			'Report Requests allow supervisors to track/report on a specific report type within a date range.',
			'When creating a request you can target all employees or select specific employees (depending on the request settings).',
			'Use the report detail page to confirm who the request targets and what period it covers.',
		])
		example('Create a report request for a department for a specific date range, then export CSV for analysis.')

		h3('13.3 Export CSV')
		bullet([
			'Use “Export CSV” to download a spreadsheet of report requests.',
			'The export includes: Requested By, Type, Start, End, Department, Targets, Created date.',
		])
		tip('CSV exports are useful for reconciliation and reporting outside the system (Excel/Sheets).')

		if is_hr_admin:
			# 13. Payroll
			h2('14. Payroll (HR/Admin)')
			h3('14.0 Payroll overview')
			bullet([
				'A payroll run generates payslips for the selected month using active salary structures.',
				'Salary vouchers are cleared/on-hold depending on pending penalties for the employee in that month.',
				'“Export cleared CSV” exports only vouchers that are Cleared.',
			])
			tip('Before creating a payroll run, confirm salary structures, pay items, penalties, and employee bank details are up to date.')

			h3('14.1 Salary structures')
			bullet([
				'Payroll → Structures: define basic salary and enable/disable structures.',
				'Each active structure is used to generate a payslip during a payroll run.',
			])
			example('Create a structure “Finance Officer” with basic salary and mark it active.')

			h3('14.2 Pay item types & employee pay items')
			bullet([
				'Pay item types define allowances/deductions categories.',
				'Employee pay items apply those types to specific employees.',
				'Use these to model recurring additions or deductions for employees.',
			])
			example('Create “Transport Allowance” as a pay item type, then apply it to an employee monthly.')

			h3('14.3 Penalties')
			bullet([
				'Penalties can be recorded and applied during payroll processing.',
				'Edit penalties if values/dates were entered incorrectly.',
				'Penalties have statuses such as Pending/Cleared/Waived. Pending penalties can cause salary vouchers to be held.',
			])
			example('Record a penalty for an incident date, apply it to the correct month, and mark it Cleared if already resolved.')

			h3('14.4 Payroll runs (generate payslips)')
			bullet([
				'Payroll → Create: start a payroll run for a month (the system normalizes it to the first day of the month).',
				'After saving, the system generates payslips for all employees with active salary structures.',
				'Open the payroll run detail page to review the payslips and voucher statuses.',
			])
			example('Create payroll run for March 2026. The run generates payslips for each active structure employee.')

			h3('14.5 Clear salary vouchers (HR/Admin)')
			bullet([
				'Clearing a voucher confirms salary payment readiness for that payslip.',
				'If the payroll run is locked, vouchers cannot be cleared.',
				'If an employee has Pending penalties for that month, clearing is blocked until penalties are resolved.',
			])
			tip('Resolve/clear/waive penalties first, then clear vouchers. This ensures deductions/holds are applied correctly.')

			h3('14.6 Export cleared CSV')
			bullet([
				'Use “Export cleared CSV” on a payroll run to download cleared vouchers only.',
				'The export includes employee name/ID and bank details (bank name, account number, branch), net pay, and voucher number.',
			])
			example('After clearing vouchers for March, export the cleared CSV and share it with Finance for bank processing.')

			# 14. Settings
			h2('15. Administration Settings (HR/Admin)')
			h3('15.1 Theme settings')
			bullet([
				'Settings → Theme: update app name, tagline, and colors (including font colors).',
				'Enable/disable branding or logo on login if required.',
				'Admin branding follows the same organization branding settings where configured.',
			])
			example('Set muted text color to a darker grey for better readability on reports.')

			h3('15.2 Access code settings')
			bullet([
				'Settings → Access Code: enable the public access code gate if your organization uses it.',
				'Set a new access code and share it securely.',
			])
			tip('Share access codes only through approved channels. Treat access codes like passwords.')
			
			h3('15.3 Business roles')
			bullet([
				'Accounts → Roles: create and manage business roles such as approval authority levels.',
				'Deactivate roles that are in use instead of deleting them.',
			])
			h3('15.4 Django Admin (advanced)')
			bullet([
				'If you have access to the Django Admin panel, use it only for advanced administration.',
				'Prefer the system pages (Employees, Payroll, Leave Types, Theme Settings) for day-to-day operations to avoid inconsistent data.',
			])

			# 15. Audit
			h2('16. Audit Logs & Notifications (HR/Admin)')
			bullet([
				'Open Audit Logs to review administrative activity.',
				'Open Notifications to view Noticeboard, Tasks, and Email alerts and mark them read.',
			])
			example('Use Audit Logs for everything else; use Notifications for Noticeboard/Tasks/Emails.')

	# 17. Troubleshooting
	h2('17. Troubleshooting & FAQ')
	h3('Login problems')
	bullet([
		'Wrong password: try again carefully (caps lock) then contact HR Admin if blocked.',
		'Account disabled: HR Admin must restore access (toggle access).',
	])

	h3('I cannot see a menu item')
	bullet([
		'Many modules are permission-based. If you need access, ask your HR Admin to confirm your role/assignment.',
	])

	h3('Document upload issues')
	bullet([
		'If upload fails, try a smaller file or a supported format.',
		'If the problem persists, report the issue to HR/Admin with the error message.',
	])

	# 18. Roles
	h2('18. Roles & Permissions Summary')
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
