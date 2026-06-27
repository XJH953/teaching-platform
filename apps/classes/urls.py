from django.urls import path
from . import views

app_name = 'classes'
urlpatterns = [
    path('', views.class_list_view, name='list'),
]
