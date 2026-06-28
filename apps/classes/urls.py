from django.urls import path
from . import views

app_name = 'classes'
urlpatterns = [
    path('', views.class_list_view, name='list'),
    path('create/', views.class_create_view, name='create'),
    path('<int:class_id>/', views.class_detail_view, name='detail'),
    path('<int:class_id>/student/<int:student_id>/delete/', views.delete_student_view, name='delete_student'),
]
