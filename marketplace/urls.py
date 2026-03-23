from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('order/create/', views.OrderCreateView.as_view(), name='order_create'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]