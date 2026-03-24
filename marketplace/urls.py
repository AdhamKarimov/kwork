from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('order/create/', views.OrderCreateView.as_view(), name='order_create'),
    path('order/<int:pk>/complete/', views.OrderCompleteView.as_view(), name='order_complete'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('my-orders/', views.MyOrdersView.as_view(), name='my_orders'),
    path('order_cancel/<int:pk>/', views.OrderCancelView.as_view(), name='order_cancel'),
]