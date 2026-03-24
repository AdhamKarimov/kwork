from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone

from .models import ChatRoom, Message, Offer
from marketplace.models import Order


class MyOffersView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        if request.user.role != 'FREELANCER':
            return redirect('marketplace:order_list')

        offers = request.user.sent_offers.select_related('room__order').order_by('-created_at')
        return render(request, 'chat/my_offers.html', {'offers': offers})


class ChatRoomDetailView(LoginRequiredMixin, View):
    """Chat xonasi — tepada loyiha tafsilotlari, pastda savdolashish bloki."""

    def get_room_or_403(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)
        if request.user not in (room.client, room.freelancer):
            raise PermissionDenied('Siz bu chat xonasiga kira olmaysiz.')
        return room

    def get(self, request, room_id):
        room     = self.get_room_or_403(request, room_id)
        messages = room.messages.select_related('sender').order_by('created_at')
        offers   = room.offers.select_related('sender').order_by('-created_at')

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

        if request.user != room.freelancer:
            raise PermissionDenied('Faqat frilanser taklif yuborishi mumkin.')

        if room.offers.filter(status='ACCEPTED').exists():
            return redirect('chat:room_detail', room_id=room_id)

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

        # Mijozga bildirishnoma — chatga o'tish linki bilan
        from notifications.services import notify_offer_received
        notify_offer_received(
            client          = room.client,
            freelancer_name = request.user.full_name,
            order_title     = room.order.title,
            order_pk        = room.order.pk,
            room_pk         = room.id,  # ← chat linki
        )

        return redirect('chat:room_detail', room_id=room_id)


class AcceptOfferView(LoginRequiredMixin, View):
    """Mijoz taklifni qabul qilganda loyiha boshlanishi va taymer ishga tushishi."""

    def post(self, request, offer_id):
        offer = get_object_or_404(Offer, id=offer_id)

        if request.user != offer.room.client:
            raise PermissionDenied('Faqat mijoz taklifni qabul qila oladi.')

        if offer.room.offers.filter(status='ACCEPTED').exists():
            return redirect('chat:room_detail', room_id=offer.room.id)

        offer.accept()

        # Frilansерga bildirishnoma — chatga o'tish linki bilan
        from notifications.services import notify_offer_accepted
        notify_offer_accepted(
            freelancer  = offer.sender,
            order_title = offer.room.order.title,
            order_pk    = offer.room.order.pk,
            room_pk     = offer.room.id,  # ← chat linki
        )

        return redirect('chat:room_detail', room_id=offer.room.id)


class SendMessageView(LoginRequiredMixin, View):
    """Chat xonasiga oddiy matn xabar yuborish."""

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        if request.user not in (room.client, room.freelancer):
            raise PermissionDenied('Siz bu chat xonasiga kira olmaysiz.')

        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                room    = room,
                sender  = request.user,
                content = content,
            )
        return redirect('chat:room_detail', room_id=room_id)


class OpenChatView(LoginRequiredMixin, View):
    """
    Frilanser buyurtma sahifasidan 'Bog'lanish' tugmasini bosadi →
    ChatRoom yaratiladi yoki mavjudi topiladi → xonaga yo'naltiriladi.
    """
    login_url = 'accounts:login'

    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)

        if request.user.role != 'FREELANCER':
            raise PermissionDenied('Faqat frilanserlar chat ocha oladi.')

        if order.status not in (Order.Status.OPEN, Order.Status.IN_NEGOTIATION):
            messages.error(request, 'Bu buyurtmaga chat ochib bo\'lmaydi.')
            return redirect('marketplace:order_detail', pk=order_id)

        # Agar IN_NEGOTIATION — boshqa frilanser bilan bo'lsa bloklash
        if order.status == Order.Status.IN_NEGOTIATION:
            existing_room = order.chat_rooms.first()
            if existing_room and existing_room.freelancer != request.user:
                messages.error(request, 'Bu buyurtma hozir boshqa frilanser bilan kelishilmoqda.')
                return redirect('marketplace:order_detail', pk=order_id)

        room, created = ChatRoom.objects.get_or_create(
            order      = order,
            freelancer = request.user,
            defaults   = {'client': order.client},
        )

        if created and order.status == Order.Status.OPEN:
            order.status = Order.Status.IN_NEGOTIATION
            order.save(update_fields=['status'])

            # Mijozga bildirishnoma — chatga o'tish linki bilan
            from notifications.services import notify_offer_received
            notify_offer_received(
                client          = order.client,
                freelancer_name = request.user.full_name,
                order_title     = order.title,
                order_pk        = order.pk,
                room_pk         = room.id,  # ← chat linki
            )

        return redirect('chat:room_detail', room_id=room.id)


class RejectOfferView(LoginRequiredMixin, View):
    def post(self, request, offer_id):
        offer = get_object_or_404(Offer, id=offer_id)

        if request.user != offer.room.client:
            raise PermissionDenied

        offer.reject()

        # Frilansерga bildirishnoma — chatga o'tish linki bilan
        from notifications.services import notify_offer_rejected
        notify_offer_rejected(
            freelancer  = offer.sender,
            order_title = offer.room.order.title,
            order_pk    = offer.room.order.pk,
            room_pk     = offer.room.id,  # ← chat linki
        )

        # Agar barcha takliflar rad etilgan bo'lsa → order OPEN ga qaytsin
        room = offer.room
        has_pending  = room.offers.filter(status='PENDING').exists()
        has_accepted = room.offers.filter(status='ACCEPTED').exists()

        if not has_pending and not has_accepted:
            order = room.order
            order.status = Order.Status.OPEN
            order.save(update_fields=['status'])

        return redirect('chat:room_detail', room_id=room.id)