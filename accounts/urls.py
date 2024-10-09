from django.urls import path

from . import views

urlpatterns = [
    path('check_login', views.check_login, name='check_login'),
    path('check_signup', views.check_signup, name='check_signup'),
    path('activate/<int:user_id>/<str:api_key>', views.activation, name='activation'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('reset_password_confirm/<uidb64>/<token>/', views.reset_password_confirm, name='reset_password_confirm'),
]
