from django.urls import path
from . import views

app_name = 'discussions'
urlpatterns = [
    path('', views.topic_list_view, name='list'),
    path('create/', views.topic_create_view, name='create'),
    path('<int:pk>/', views.topic_detail_view, name='detail'),
    path('<int:pk>/reply/', views.reply_create_view, name='reply'),
]
