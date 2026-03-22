from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-code/', views.ResendCodeView.as_view(), name='resend_code'),
]