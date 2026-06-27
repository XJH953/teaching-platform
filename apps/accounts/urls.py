from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.login_view, name='login'),
    path('first-login/', views.first_login_view, name='first_login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
