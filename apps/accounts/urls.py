from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'
urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
