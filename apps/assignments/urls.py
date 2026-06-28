from django.urls import path
from . import views

app_name = 'assignments'
urlpatterns = [
    # Teacher URLs
    path('', views.task_list_view, name='list'),
    path('analytics/', views.grade_analytics_view, name='analytics'),
    path('create/', views.task_create_view, name='create'),
    path('<int:pk>/', views.task_detail_view, name='detail'),
    path('<int:pk>/delete/', views.delete_task_view, name='delete'),
    path('<int:pk>/submissions/', views.submission_list_view, name='submissions'),
    path('<int:task_pk>/grade/<int:submission_pk>/', views.grade_submission_view, name='grade'),

    # Student URLs
    path('my/', views.student_task_list_view, name='student_list'),
    path('<int:pk>/submit/', views.student_task_detail_view, name='student_submit'),
]
