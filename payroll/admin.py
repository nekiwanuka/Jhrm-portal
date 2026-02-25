from django.contrib import admin

from .models import (
	EmployeePayItem,
	PayItemType,
	PayrollRun,
	Payslip,
	Penalty,
	SalaryStructure,
	SalaryVoucher,
)

admin.site.register(SalaryStructure)
admin.site.register(PayItemType)
admin.site.register(EmployeePayItem)
admin.site.register(Penalty)
admin.site.register(PayrollRun)
admin.site.register(Payslip)
admin.site.register(SalaryVoucher)
