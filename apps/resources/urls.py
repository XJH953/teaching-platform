from django.urls import path
from . import views

app_name = 'resources'
urlpatterns = [
    path('', views.resource_list_view, name='list'),       # public browse (Task 3)
    path('my/', views.my_resource_list_view, name='my_list'),  # teacher's own
    path('create/', views.resource_create_view, name='create'),
    path('<int:pk>/edit/', views.resource_edit_view, name='edit'),
    path('<int:pk>/delete/', views.resource_delete_view, name='delete'),
    path('<int:pk>/', views.resource_detail_view, name='detail'),  # Task 3
]
