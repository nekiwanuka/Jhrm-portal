from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from core.permissions import SupervisorPlusRequiredMixin

from .forms import PerformanceReviewForm
from .models import PerformanceReview


class PerformanceReviewListView(LoginRequiredMixin, SupervisorPlusRequiredMixin, ListView):
	model = PerformanceReview
	template_name = 'performance/review_list.html'
	context_object_name = 'reviews'


class PerformanceReviewCreateView(LoginRequiredMixin, SupervisorPlusRequiredMixin, CreateView):
	model = PerformanceReview
	form_class = PerformanceReviewForm
	template_name = 'common/form.html'
	success_url = reverse_lazy('performance:list')

	def form_valid(self, form):
		form.instance.reviewer = self.request.user
		return super().form_valid(form)
