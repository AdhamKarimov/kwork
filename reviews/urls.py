from django.urls import path
from . import views

app_name = 'reviews'


urlpatterns = [
    # Buyurtma bo'yicha sharh qoldirish
    path('order/<int:order_id>/add/', views.CreateReviewView.as_view(), name='create_review'),
]