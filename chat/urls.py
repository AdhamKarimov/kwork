from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('room/<int:room_id>/',         views.ChatRoomDetailView.as_view(), name='room_detail'),
    path('room/<int:room_id>/message/', views.SendMessageView.as_view(),   name='send_message'),
    path('room/<int:room_id>/offer/',   views.SendOfferView.as_view(),     name='send_offer'),
    path('offer/<int:offer_id>/accept/',views.AcceptOfferView.as_view(),   name='accept_offer'),
    path('open/<int:order_id>/',        views.OpenChatView.as_view(),      name='open_chat'),
    path('offer/<int:offer_id>/reject/', views.RejectOfferView.as_view(), name='reject_offer'),
    path('my-offers/', views.MyOffersView.as_view(), name='my_offers'),
]