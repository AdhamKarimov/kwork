from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import ChatRoom, Message, Offer
from marketplace.models import Order


class ChatRoomDetailView(LoginRequiredMixin, View):
    """Chat xonasi — tepada loyiha tafsilotlari, pastda savdolashish bloki."""

    def get_room_or_403(self, request, room_id):
        """Xonani olish va foydalanuvchi ruxsatini tekshirish."""
        room = get_object_or_404(ChatRoom, id=room_id)
        if request.user not in (room.client, room.freelancer):
            raise PermissionDenied('Siz bu chat xonasiga kira olmaysiz.')
        return room

    def get(self, request, room_id):
        room     = self.get_room_or_403(request, room_id)
        messages = room.messages.select_related('sender').order_by('created_at')
        offers   = room.offers.select_related('sender').order_by('-created_at')

        # Countdown uchun vaqtni hisoblash
        time_left  = None
        is_expired = False

        if room.order.status == Order.Status.IN_PROGRESS and room.order.deadline:
            delta = room.order.deadline - timezone.now()
            if delta.total_seconds() > 0:
                time_left = delta
            else:
                is_expired = True

        return render(request, 'chat/room.html', {
            'room':       room,
            'messages':   messages,
            'offers':     offers,
            'time_left':  time_left,
            'is_expired': is_expired,
        })


class SendOfferView(LoginRequiredMixin, View):
    """Frilanser taklif yuborishi."""

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        # Faqat shu xonaning frilanseri taklif yubora oladi
        if request.user != room.freelancer:
            raise PermissionDenied('Faqat frilanser taklif yuborishi mumkin.')

        # Allaqachon qabul qilingan taklif bo'lsa yangi taklif yubora olmaydi
        if room.offers.filter(status='ACCEPTED').exists():
            return redirect('chat:room_detail', room_id=room_id)

        # Qiymatlarni olish va validatsiya
        try:
            proposed_price = float(request.POST.get('price', 0))
            delivery_days  = int(request.POST.get('days', 0))
        except (ValueError, TypeError):
            return render(request, 'chat/room.html', {
                'room':  room,
                'error': 'Narx va kun to\'g\'ri kiritilishi kerak.',
            })

        if proposed_price <= 0 or delivery_days <= 0:
            return render(request, 'chat/room.html', {
                'room':  room,
                'error': 'Narx va kun musbat son bo\'lishi kerak.',
            })

        message = request.POST.get('message', '').strip()

        Offer.objects.create(
            room           = room,
            sender         = request.user,
            proposed_price = proposed_price,
            delivery_days  = delivery_days,
            message        = message,
        )
        return redirect('chat:room_detail', room_id=room_id)


class AcceptOfferView(LoginRequiredMixin, View):
    """Mijoz taklifni qabul qilganda loyiha boshlanishi va taymer ishga tushishi."""

    def post(self, request, offer_id):
        offer = get_object_or_404(Offer, id=offer_id)

        # Faqat shu xonaning mijozi qabul qila oladi
        if request.user != offer.room.client:
            raise PermissionDenied('Faqat mijoz taklifni qabul qila oladi.')

        # Allaqachon qabul qilingan taklif bo'lsa qayta qabul qilinmaydi
        if offer.room.offers.filter(status='ACCEPTED').exists():
            return redirect('chat:room_detail', room_id=offer.room.id)

        # offer.accept() ichida:
        # order.status = IN_PROGRESS va deadline = now + delivery_days
        offer.accept()

        return redirect('chat:room_detail', room_id=offer.room.id)