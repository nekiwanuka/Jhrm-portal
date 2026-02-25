from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.permissions import SupervisorPlusRequiredMixin

from .forms import EventForm
from .models import Event


class EventCalendarView(ListView):
	model = Event
	template_name = 'calendar_app/calendar_month.html'
	context_object_name = 'events'

	def get_queryset(self):
		return Event.objects.filter(is_public=True)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		today = timezone.localdate()
		context['upcoming_events'] = Event.objects.filter(start_date__gte=today, is_public=True)[:6]
		user = self.request.user
		context['can_manage_events'] = user.is_authenticated and (
			user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}
		)
		return context


class EventCreateView(LoginRequiredMixin, SupervisorPlusRequiredMixin, CreateView):
	model = Event
	form_class = EventForm
	template_name = 'calendar_app/event_form.html'
	success_url = reverse_lazy('calendar_app:month')

	def form_valid(self, form):
		form.instance.created_by = self.request.user
		return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, SupervisorPlusRequiredMixin, UpdateView):
	model = Event
	form_class = EventForm
	template_name = 'calendar_app/event_form.html'
	success_url = reverse_lazy('calendar_app:month')


class EventDeleteView(LoginRequiredMixin, SupervisorPlusRequiredMixin, DeleteView):
	model = Event
	template_name = 'calendar_app/event_confirm_delete.html'
	success_url = reverse_lazy('calendar_app:month')
