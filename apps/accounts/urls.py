from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.login_view, name='login'),
    path('first-login/', views.first_login_view, name='first_login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('logout/', views.logout_view, name='logout'),
    path('reset-password/<int:student_id>/', views.reset_password_view, name='reset_password'),
    path('change-password/', views.change_password_view, name='change_password'),
]
