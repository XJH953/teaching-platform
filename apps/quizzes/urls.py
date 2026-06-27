from django.urls import path
from . import views

app_name = 'quizzes'
urlpatterns = [
    path('', views.quiz_list_view, name='list'),
    path('create/', views.quiz_create_view, name='create'),
    path('<int:pk>/questions/', views.add_questions_view, name='add_questions'),
    path('<int:pk>/results/', views.quiz_results_view, name='results'),
    path('<int:pk>/take/', views.take_quiz_view, name='take'),
]
