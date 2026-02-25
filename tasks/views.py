from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.permissions import SupervisorPlusRequiredMixin
from audit.models import AuditLog
from audit.models import Notification
from django.contrib.auth import get_user_model
from django.db.models import Q

from .forms import TaskForm
from .models import Task


def _can_manage_tasks(user):
	return user.is_authenticated and (
		user.is_superuser or user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}
	)


def _can_drag_board(user):
	return user.is_authenticated


def _visible_tasks_q(user):
	"""Returns a Q() limiting tasks to what the user is allowed to see."""
	if not user.is_authenticated:
		return Q(visibility=Task.VISIBILITY_ALL)
	if _can_manage_tasks(user):
		return Q()
	return Q(visibility=Task.VISIBILITY_ALL) | Q(visible_to=user) | Q(assigned_to=user) | Q(created_by=user)


def _user_can_access_task(user, task: Task) -> bool:
	if not user.is_authenticated:
		return task.visibility == Task.VISIBILITY_ALL
	if _can_manage_tasks(user):
		return True
	if task.visibility == Task.VISIBILITY_ALL:
		return True
	return (task.visible_to_id == user.id) or (task.assigned_to_id == user.id) or (task.created_by_id == user.id)


def _admin_recipients():
	User = get_user_model()
	return list(User.objects.filter(Q(is_superuser=True) | Q(role__in={'SUPER_ADMIN', 'HR_MANAGER'})).only('id'))


class TaskBoardView(ListView):
	model = Task
	template_name = 'tasks/task_board.html'
	context_object_name = 'tasks'

	def get_queryset(self):
		return Task.objects.filter(_visible_tasks_q(self.request.user))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		today = timezone.localdate()
		visible_q = _visible_tasks_q(self.request.user)
		total = Task.objects.filter(visible_q).count()
		done = Task.objects.filter(visible_q, status=Task.STATUS_DONE).count()
		completion_rate = round((done / total) * 100, 2) if total else 0
		overdue = Task.objects.filter(visible_q, Q(deadline__lt=today) & ~Q(status=Task.STATUS_DONE)).count()
		context['kpis'] = {
			'total': total,
			'done': done,
			'completion_rate': completion_rate,
			'overdue': overdue,
		}
		context['todo_tasks'] = Task.objects.filter(visible_q, status=Task.STATUS_TODO)
		context['in_progress_tasks'] = Task.objects.filter(visible_q, status=Task.STATUS_IN_PROGRESS)
		context['done_tasks'] = Task.objects.filter(visible_q, status=Task.STATUS_DONE)
		context['redo_tasks'] = Task.objects.filter(visible_q, status=Task.STATUS_REDO)
		for key in ['todo_tasks', 'in_progress_tasks', 'done_tasks', 'redo_tasks']:
			context[key] = context[key].order_by('position', 'deadline', '-created_at')
		can_view_staff_perf = self.request.user.is_authenticated and (
			self.request.user.is_superuser or self.request.user.role in {'SUPER_ADMIN', 'HR_MANAGER'}
		)
		context['can_manage_tasks'] = self.request.user.is_authenticated and (
			self.request.user.is_superuser or self.request.user.role in {'SUPER_ADMIN', 'HR_MANAGER', 'SUPERVISOR'}
		)
		context['can_view_staff_perf'] = can_view_staff_perf
		context['staff_performance'] = (
			Task.objects.filter(visible_q).values('assigned_to__username')
			.annotate(avg_progress=Avg('progress'), task_count=Count('id'))
			.order_by('-avg_progress')
			if can_view_staff_perf
			else []
		)
		return context


class TaskCreateView(LoginRequiredMixin, SupervisorPlusRequiredMixin, CreateView):
	model = Task
	form_class = TaskForm
	template_name = 'tasks/task_form.html'
	success_url = reverse_lazy('tasks:board')

	def form_valid(self, form):
		form.instance.created_by = self.request.user
		if form.instance.visibility == Task.VISIBILITY_USER and not form.instance.visible_to_id and form.instance.assigned_to_id:
			form.instance.visible_to = form.instance.assigned_to
		status = form.cleaned_data.get('status') or Task.STATUS_TODO
		max_pos = Task.objects.filter(status=status).aggregate(max_pos=models.Max('position')).get('max_pos')
		form.instance.position = (max_pos or 0) + 1
		return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, SupervisorPlusRequiredMixin, UpdateView):
	model = Task
	form_class = TaskForm
	template_name = 'tasks/task_form.html'
	success_url = reverse_lazy('tasks:board')


class TaskDeleteView(LoginRequiredMixin, SupervisorPlusRequiredMixin, DeleteView):
	model = Task
	template_name = 'tasks/task_confirm_delete.html'
	success_url = reverse_lazy('tasks:board')


@login_required
@require_POST
def move_task(request, pk):
	# We log this action ourselves (with details), so skip the generic middleware log.
	request.skip_audit_log = True

	if not _can_drag_board(request.user):
		return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

	task = get_object_or_404(Task, pk=pk)
	if not _user_can_access_task(request.user, task):
		return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
	old_status = task.status

	new_status = None
	if request.content_type == 'application/json':
		try:
			import json
			payload = json.loads(request.body.decode('utf-8') or '{}')
			new_status = payload.get('status')
		except Exception:
			new_status = None
	else:
		new_status = request.POST.get('status')

	allowed_statuses = {
		Task.STATUS_TODO,
		Task.STATUS_IN_PROGRESS,
		Task.STATUS_DONE,
		Task.STATUS_REDO,
	}
	if new_status not in allowed_statuses:
		return JsonResponse({'ok': False, 'error': 'invalid_status'}, status=400)

	if task.status == new_status:
		return JsonResponse({'ok': True, 'status': task.status})

	new_position = (
		Task.objects.filter(status=new_status).exclude(pk=task.pk).aggregate(max_pos=models.Max('position')).get('max_pos')
	)
	new_position = (new_position or 0) + 1

	task.status = new_status
	task.position = new_position
	task.save(update_fields=['status', 'position'])

	AuditLog.objects.create(
		user=request.user,
		action=f'TASK MOVE: "{task.title}" (#{task.pk}) {old_status} -> {new_status}',
		path=request.path,
		method='POST',
		status_code=200,
	)

	admins = _admin_recipients()
	if admins:
		Notification.objects.bulk_create(
			[
				Notification(
					recipient=a,
					actor=request.user,
					message=f'Task moved: "{task.title}" ({old_status} → {new_status})',
					path=request.path,
					level=Notification.LEVEL_INFO,
				)
				for a in admins
				if a.id != request.user.id
			]
		)
	return JsonResponse({'ok': True, 'status': task.status, 'position': task.position})


@login_required
@require_POST
def reorder_tasks(request):
	# We log this action ourselves (with details), so skip the generic middleware log.
	request.skip_audit_log = True

	if not _can_drag_board(request.user):
		return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

	try:
		import json
		payload = json.loads(request.body.decode('utf-8') or '{}')
	except Exception:
		payload = {}

	status = payload.get('status')
	ordered_ids = payload.get('ordered_ids')
	if not status or not isinstance(ordered_ids, list):
		return JsonResponse({'ok': False, 'error': 'invalid_payload'}, status=400)

	allowed_statuses = {
		Task.STATUS_TODO,
		Task.STATUS_IN_PROGRESS,
		Task.STATUS_DONE,
		Task.STATUS_REDO,
	}
	if status not in allowed_statuses:
		return JsonResponse({'ok': False, 'error': 'invalid_status'}, status=400)

	try:
		ordered_ids_int = [int(x) for x in ordered_ids]
	except Exception:
		return JsonResponse({'ok': False, 'error': 'invalid_ids'}, status=400)

	# Ensure all tasks exist and belong to the requested status
	visible_q = _visible_tasks_q(request.user)
	tasks = list(Task.objects.filter(visible_q, id__in=ordered_ids_int, status=status).only('id', 'position'))
	if len(tasks) != len(set(ordered_ids_int)):
		return JsonResponse({'ok': False, 'error': 'mismatch'}, status=400)

	task_by_id = {t.id: t for t in tasks}
	for idx, task_id in enumerate(ordered_ids_int, start=1):
		task_by_id[task_id].position = idx

	Task.objects.bulk_update(tasks, ['position'])

	AuditLog.objects.create(
		user=request.user,
		action=f'TASK REORDER: {status} ({len(ordered_ids_int)} cards)',
		path=request.path,
		method='POST',
		status_code=200,
	)

	admins = _admin_recipients()
	if admins:
		Notification.objects.bulk_create(
			[
				Notification(
					recipient=a,
					actor=request.user,
					message=f'Tasks reordered: {status} ({len(ordered_ids_int)} cards)',
					path=request.path,
					level=Notification.LEVEL_INFO,
				)
				for a in admins
				if a.id != request.user.id
			]
		)
	return JsonResponse({'ok': True})
