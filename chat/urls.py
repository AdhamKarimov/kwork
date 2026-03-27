from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('open/<int:order_id>/',views.OpenChatView.as_view(),         name='open_chat'),
    path('room/<int:room_id>/',views.ChatRoomDetailView.as_view(),   name='room_detail'),
    path('room/<int:room_id>/send/',views.SendMessageView.as_view(),      name='send_message'),
    path('room/<int:room_id>/offer/', views.SendOfferView.as_view(),        name='send_offer'),
    path('room/<int:room_id>/submit/',views.SubmitWorkView.as_view(),       name='submit_work'),
    path('offer/<int:offer_id>/accept/',views.AcceptOfferView.as_view(),      name='accept_offer'),
    path('offer/<int:offer_id>/reject/',views.RejectOfferView.as_view(),      name='reject_offer'),
    path('order/<int:order_id>/offers/', views.OrderOffersView.as_view(),      name='order_offers'),
    path('submission/<int:submission_id>/review/', views.ReviewSubmissionView.as_view(), name='review_submission'),
    path('my-offers/',views.MyOffersView.as_view(),         name='my_offers'),
]