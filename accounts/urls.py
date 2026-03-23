from django.urls import path
from . import views

app_name = 'accounts'


urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-code/', views.ResendCodeView.as_view(), name='resend_code'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_out, name='logout'),
]