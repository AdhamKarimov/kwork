from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('mark-read/<int:pk>/', views.MarkAsReadView.as_view(), name='mark_read'),
]