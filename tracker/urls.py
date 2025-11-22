from django.urls import path
from . import views

urlpatterns = [
    path('api/login/', views.api_login, name='api_login'),

    path('projects/', views.create_project, name='create_project'),  # handles GET + POST

    path('projects/<int:project_id>/tasks/', views.create_task, name='create_task'),

    path('tasks/', views.list_tasks, name='list_tasks'),

    path('dashboard/', views.dashboard, name='dashboard'),
]
