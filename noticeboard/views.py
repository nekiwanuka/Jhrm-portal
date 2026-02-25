from datetime import date

from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.permissions import HRAdminRequiredMixin

from .forms import NoticeCommentForm, NoticeForm
from .models import Notice, NoticeComment


def user_can_manage_notices(user):
	return user.is_authenticated and (user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER'})


class NoticeListView(ListView):
	model = Notice
	template_name = 'noticeboard/notice_list.html'
	context_object_name = 'notices'
	paginate_by = 10

	def get_queryset(self):
		today = date.today()
		return Notice.objects.select_related('created_by').filter(Q(expiry_date__isnull=True) | Q(expiry_date__gte=today), is_public=True)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		context['can_manage_notices'] = user_can_manage_notices(user)
		return context


class NoticeCreateView(LoginRequiredMixin, CreateView):
	model = Notice
	form_class = NoticeForm
	template_name = 'noticeboard/notice_form.html'
	success_url = reverse_lazy('noticeboard:list')

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

	def form_valid(self, form):
		user = self.request.user
		form.instance.created_by = user
		form.instance.created_by_name = user.get_full_name() or user.username or ''
		form.instance.created_by_phone = getattr(user, 'phone_number', '') or ''
		department_name = ''
		position_title = ''
		try:
			profile = user.employee_profile
			if getattr(profile, 'department_id', None) and profile.department:
				department_name = profile.department.name
			if getattr(profile, 'position_id', None) and profile.position:
				position_title = profile.position.title
		except Exception:
			pass
		form.instance.created_by_department = department_name
		form.instance.created_by_position = position_title
		return super().form_valid(form)


class NoticeDetailView(DetailView):
	model = Notice
	template_name = 'noticeboard/notice_detail.html'
	context_object_name = 'notice'

	def get_queryset(self):
		qs = Notice.objects.select_related('created_by').prefetch_related('comments__user')
		if user_can_manage_notices(self.request.user):
			return qs
		today = date.today()
		return qs.filter(Q(expiry_date__isnull=True) | Q(expiry_date__gte=today), is_public=True)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['can_manage_notices'] = user_can_manage_notices(self.request.user)
		context['comment_form'] = NoticeCommentForm()
		return context


@login_required
@require_POST
def add_notice_comment(request, pk):
	notice = get_object_or_404(Notice, pk=pk)
	if not user_can_manage_notices(request.user):
		# Enforce the same visibility rules as the public list.
		if not notice.is_public:
			raise Http404
		if notice.expiry_date and notice.expiry_date < date.today():
			raise Http404

	form = NoticeCommentForm(request.POST)
	if form.is_valid():
		comment = form.save(commit=False)
		comment.notice = notice
		comment.user = request.user
		comment.save()

	return redirect('noticeboard:detail', pk=notice.pk)


class NoticeUpdateView(LoginRequiredMixin, HRAdminRequiredMixin, UpdateView):
	model = Notice
	form_class = NoticeForm
	template_name = 'noticeboard/notice_form.html'
	success_url = reverse_lazy('noticeboard:list')

	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs


class NoticeDeleteView(LoginRequiredMixin, HRAdminRequiredMixin, DeleteView):
	model = Notice
	template_name = 'noticeboard/notice_confirm_delete.html'
	success_url = reverse_lazy('noticeboard:list')
