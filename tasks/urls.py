from django.urls import path

from .views import TaskBoardView, TaskCreateView, TaskDeleteView, TaskUpdateView, move_task, reorder_tasks

app_name = 'tasks'

urlpatterns = [
    path('', TaskBoardView.as_view(), name='board'),
    path('create/', TaskCreateView.as_view(), name='create'),
    path('<int:pk>/move/', move_task, name='move'),
    path('reorder/', reorder_tasks, name='reorder'),
    path('<int:pk>/edit/', TaskUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', TaskDeleteView.as_view(), name='delete'),
]
