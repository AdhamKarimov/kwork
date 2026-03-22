from django.urls import path
from . import views

urlpatterns = [
    # Chat xonasiga kirish
    path('room/<int:room_id>/', views.ChatRoomDetailView.as_view(), name='room_detail'),
    
    # TZ: Frilanser taklif yuborishi
    path('room/<int:room_id>/offer/send/', views.SendOfferView.as_view(), name='send_offer'),
    
    # TZ: Mijoz taklifni qabul qilishi (Loyiha va Taymer boshlanishi)
    path('offer/<int:offer_id>/accept/', views.AcceptOfferView.as_view(), name='accept_offer'),
    
    # Chat xonasi yaratish (Marketplace'dan o'tilganda)
    path('create-room/<int:order_id>/', views.CreateChatRoomView.as_view(), name='create_room'),
]