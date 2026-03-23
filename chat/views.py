from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ChatRoom, Message, Offer
from marketplace.models import Order
from django.utils import timezone

class ChatRoomDetailView(LoginRequiredMixin, View):
    """TZ 4-bandi: Chat interfeysi, tepada loyiha tafsilotlari va pastda savdolashish bloki"""
    def get(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)
        messages = room.messages.all()
        offers = room.offers.all()
        
        # TZ B-bandi: Countdown uchun vaqtni hisoblash
        time_left = None
        if room.order.status == Order.Status.IN_PROGRESS and room.order.deadline:
            time_left = room.order.deadline - timezone.now()
            if time_left.total_seconds() < 0:
                time_left = "Vaqt tugadi"

        return render(request, 'chat/room.html', {
            'room': room,
            'messages': messages,
            'offers': offers,
            'time_left': time_left
        })

class SendOfferView(LoginRequiredMixin, View):
    """TZ A-bandi: Frilanser taklif yuborishi"""
    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)
        if request.user.role == 'FREELANCER':
            Offer.objects.create(
                room=room,
                sender=request.user,
                proposed_price=request.POST.get('price'),
                delivery_days=request.POST.get('days'),
                message=request.POST.get('message')
            )
        return redirect('chat:room_detail', room_id=room_id)

class AcceptOfferView(LoginRequiredMixin, View):
    """TZ A-bandi: Mijoz qabul qilganda loyiha boshlanishi va taymer ishga tushishi"""
    def post(self, request, offer_id):
        offer = get_object_or_404(Offer, id=offer_id)
        if offer.room.client == request.user:
            # Sening modelingdagi offer.accept() metodi ishga tushadi
            # U yerda order.status = IN_PROGRESS va deadline = now + days mantiqi bor
            offer.accept()
        return redirect('chat:room_detail', room_id=offer.room.id)
    
class CreateChatRoomView(LoginRequiredMixin, View):
    """
    TZ: Frilanser buyurtma bo'yicha muloqot boshlashi uchun.
    Agar xona oldin yaratilgan bo'lsa, mavjudiga yo'naltiradi.
    """
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        
        if order.client == request.user:
            return redirect('marketplace:order_detail', pk=order_id)

        if request.user.role != 'FREELANCER':
            return redirect('marketplace:order_detail', pk=order_id)

        room, created = ChatRoom.objects.get_or_create(
            order=order,
            freelancer=request.user,
            defaults={'client': order.client}
        )
        
        return redirect('chat:room_detail', room_id=room.id)