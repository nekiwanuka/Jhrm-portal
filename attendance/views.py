from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from core.permissions import SupervisorPlusRequiredMixin

from .forms import AttendanceRecordForm
from .models import AttendanceRecord


class AttendanceListView(LoginRequiredMixin, SupervisorPlusRequiredMixin, ListView):
	model = AttendanceRecord
	template_name = 'attendance/attendance_list.html'
	context_object_name = 'records'


class AttendanceCreateView(LoginRequiredMixin, SupervisorPlusRequiredMixin, CreateView):
	model = AttendanceRecord
	form_class = AttendanceRecordForm
	template_name = 'attendance/attendance_form.html'
	success_url = reverse_lazy('attendance:list')
