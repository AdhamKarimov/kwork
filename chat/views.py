from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from .models import Submission
from .models import ChatRoom, Message, Offer
from marketplace.models import Order


class OpenChatView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)

        if request.user.role != 'FREELANCER':
            raise PermissionDenied('Faqat frilanserlar chat ocha oladi.')

        if order.status not in [Order.Status.OPEN, Order.Status.IN_NEGOTIATION]:
            messages.error(request, 'Bu buyurtmaga taklif berish mumkin emas.')
            return redirect('marketplace:order_detail', pk=order_id)

        room, created = ChatRoom.objects.get_or_create(
            order      = order,
            freelancer = request.user,
            defaults   = {'client': order.client},
        )

        if created:
            from notifications.services import notify_new_chat
            notify_new_chat(
                client          = order.client,
                freelancer_name = request.user.full_name,
                order_title     = order.title,
                order_pk        = order.pk,
            )

        return redirect('chat:room_detail', room_id=room.id)


class SendOfferView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        if request.user != room.freelancer:
            raise PermissionDenied('Faqat frilanser taklif yuborishi mumkin.')

        if room.is_blocked:
            messages.error(request, 'Siz bu loyiha uchun taklif yubora olmaysiz (3 marta rad etildi).')
            return redirect('chat:room_detail', room_id=room_id)

        if room.offers.filter(status=Offer.Status.ACCEPTED).exists():
            messages.warning(request, 'Bu loyiha uchun taklif allaqachon qabul qilingan.')
            return redirect('chat:room_detail', room_id=room_id)

        if room.offers.filter(status=Offer.Status.PENDING).exists():
            messages.warning(request, "Sizning taklifingiz hali ko'rib chiqilmoqda.")
            return redirect('chat:room_detail', room_id=room_id)

        try:
            proposed_price = float(request.POST.get('price', 0))
            delivery_days  = int(request.POST.get('days', 0))
        except (ValueError, TypeError):
            messages.error(request, "Narx va kun to'g'ri kiritilishi kerak.")
            return redirect('chat:room_detail', room_id=room_id)

        if proposed_price <= 0 or delivery_days <= 0:
            messages.error(request, "Narx va kun musbat son bo'lishi kerak.")
            return redirect('chat:room_detail', room_id=room_id)

        message_text = request.POST.get('message', '').strip()

        Offer.objects.create(
            room           = room,
            sender         = request.user,
            proposed_price = proposed_price,
            delivery_days  = delivery_days,
            message        = message_text,
        )

        order = room.order
        if order.status == Order.Status.OPEN:
            order.status = Order.Status.IN_NEGOTIATION
            order.save(update_fields=['status'])

        from notifications.services import notify_offer_received
        notify_offer_received(
            client          = room.client,
            freelancer_name = request.user.full_name,
            order_title     = room.order.title,
            order_pk        = room.order.pk,
            room_pk         = room.id,
        )

        messages.success(request, 'Taklifingiz yuborildi!')
        return redirect('chat:room_detail', room_id=room_id)


class OrderOffersView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)

        if request.user != order.client:
            raise PermissionDenied("Faqat loyiha egasi takliflarni ko'ra oladi.")

        rooms = (
            order.chat_rooms
            .select_related('freelancer')
            .prefetch_related('offers')
            .order_by('-created_at')
        )

        rooms_data = []
        for room in rooms:
            offers         = room.offers.order_by('-created_at')
            rejected_count = offers.filter(status='REJECTED').count()
            rooms_data.append({
                'room':           room,
                'last_offer':     offers.first(),
                'rejected_count': rejected_count,
                'is_blocked':     rejected_count >= 3,
            })

        return render(request, 'chat/order_offers.html', {
            'order':      order,
            'rooms_data': rooms_data,
        })


class AcceptOfferView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, offer_id):
        offer = get_object_or_404(Offer, id=offer_id)
        order = offer.room.order

        if request.user != order.client:
            raise PermissionDenied('Faqat loyiha egasi taklifni qabul qila oladi.')

        if order.chat_rooms.filter(offers__status=Offer.Status.ACCEPTED).exists():
            messages.warning(request, 'Bu loyiha uchun taklif allaqachon qabul qilingan.')
            return redirect('chat:order_offers', order_id=order.pk)

        offer.accept()

        messages.success(
            request,
            f"{offer.sender.full_name}ning taklifi qabul qilindi! Loyiha boshlandi."
        )
        return redirect('chat:room_detail', room_id=offer.room.id)


class RejectOfferView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, offer_id):
        offer = get_object_or_404(Offer, id=offer_id)
        order = offer.room.order

        if request.user != order.client:
            raise PermissionDenied('Faqat loyiha egasi taklifni rad eta oladi.')

        offer.reject()

        from notifications.services import notify_offer_rejected
        notify_offer_rejected(
            freelancer  = offer.sender,
            order_title = order.title,
            order_pk    = order.pk,
            room_pk     = offer.room.id,
        )

        messages.info(request, 'Taklif rad etildi.')
        return redirect('chat:room_detail', room_id=offer.room.id)


class ChatRoomDetailView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get_room_or_403(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)
        if request.user not in (room.client, room.freelancer):
            raise PermissionDenied('Siz bu chat xonasiga kira olmaysiz.')
        return room

    def get(self, request, room_id):
        room   = self.get_room_or_403(request, room_id)
        msgs   = room.messages.select_related('sender').order_by('created_at')
        offers = room.offers.select_related('sender').order_by('-created_at')
        active_submission = room.submissions.filter(
            status=Submission.Status.PENDING
        ).last()
        last_submission = room.submissions.order_by('-created_at').first()

        time_left  = None
        is_expired = False

        if room.order.status == Order.Status.IN_PROGRESS and room.order.deadline:
            delta = room.order.deadline - timezone.now()
            if delta.total_seconds() > 0:
                time_left = delta
            else:
                is_expired = True

        can_send_offer = (
            request.user == room.freelancer
            and room.order.status in [Order.Status.OPEN, Order.Status.IN_NEGOTIATION]
            and not room.is_blocked
            and not room.offers.filter(status=Offer.Status.PENDING).exists()
            and not room.offers.filter(status=Offer.Status.ACCEPTED).exists()
        )

        return render(request, 'chat/room.html', {
            'room':           room,
            'messages':       msgs,
            'offers':         offers,
            'time_left':      time_left,
            'is_expired':     is_expired,
            'can_send_offer': can_send_offer,
            'active_submission': active_submission,
            'last_submission': last_submission,
        })


class SendMessageView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        if request.user not in (room.client, room.freelancer):
            raise PermissionDenied('Siz bu chat xonasiga kira olmaysiz.')

        if request.user == room.freelancer and room.is_blocked:
            messages.error(request, 'Siz bu loyiha chatiga xabar yubora olmaysiz.')
            return redirect('chat:room_detail', room_id=room_id)

        content = request.POST.get('content', '').strip()

        if content:
            Message.objects.create(room=room, sender=request.user, content=content)

            receiver = room.freelancer if request.user == room.client else room.client

            from notifications.models import Notification
            Notification.objects.create(
                user    = receiver,
                type    = 'MESSAGE',
                message = f"{request.user.full_name}: {content[:40]}",
                link    = f"/chat/room/{room.id}/",
            )

        return redirect('chat:room_detail', room_id=room_id)


class MyOffersView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        if request.user.role != 'FREELANCER':
            return redirect('marketplace:order_list')

        offers = (
            request.user.sent_offers
            .select_related('room__order')
            .order_by('-created_at')
        )
        return render(request, 'chat/my_offers.html', {'offers': offers})


# ─────────────────────────────────────────────────────────
# 9. FRILANSER — ISH TOPSHIRISH
# ─────────────────────────────────────────────────────────
class SubmitWorkView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)

        if request.user != room.freelancer:
            raise PermissionDenied('Faqat frilanser ish topshira oladi.')

        if room.order.status != Order.Status.IN_PROGRESS:
            messages.error(request, 'Faqat jarayondagi loyihani topshirish mumkin.')
            return redirect('chat:room_detail', room_id=room_id)

        # Allaqachon pending topshiriq bormi?
        if room.submissions.filter(status='PENDING').exists():
            messages.warning(request, "Topshiriqingiz hali ko'rib chiqilmoqda.")
            return redirect('chat:room_detail', room_id=room_id)

        file    = request.FILES.get('file')
        comment = request.POST.get('comment', '').strip()

        if not file:
            messages.error(request, 'Fayl yuklanmadi.')
            return redirect('chat:room_detail', room_id=room_id)

        from .models import Submission
        Submission.objects.create(
            room       = room,
            freelancer = request.user,
            file       = file,
            comment    = comment,
        )

        from notifications.services import notify_work_submitted
        notify_work_submitted(
            client          = room.client,
            freelancer_name = request.user.full_name,
            order_title     = room.order.title,
            order_pk        = room.order.pk,
            room_pk         = room.id,
        )

        messages.success(request, 'Ish topshirildi! Mijoz ko\'rib chiqadi.')
        return redirect('chat:room_detail', room_id=room_id)


# ─────────────────────────────────────────────────────────
# 10. MIJOZ — TOPSHIRIQNI KO'RIB CHIQISH (tasdiqlash/rad)
# ─────────────────────────────────────────────────────────
class ReviewSubmissionView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, submission_id):
        from .models import Submission
        submission = get_object_or_404(Submission, id=submission_id)
        room       = submission.room

        if request.user != room.client:
            raise PermissionDenied('Faqat mijoz topshiriqni ko\'rib chiqishi mumkin.')

        action      = request.POST.get('action')  # 'approve' yoki 'reject'
        client_note = request.POST.get('client_note', '').strip()

        if action == 'approve':
            try:
                rating = int(request.POST.get('rating', 5))
                rating = max(1, min(5, rating))  # 1-5 oralig'ida
            except (ValueError, TypeError):
                rating = 5

            submission.approve(rating=rating, client_note=client_note)
            messages.success(request, f'Ish tasdiqlandi! Frilanserga {rating}⭐ baho berildi.')

        elif action == 'reject':
            if not client_note:
                messages.error(request, "Qayta ishlash sababini yozing.")
                return redirect('chat:room_detail', room_id=room.id)
            submission.reject_work(client_note=client_note)
            messages.info(request, 'Frilanserga qayta ishlash so\'rovi yuborildi.')

        return redirect('chat:room_detail', room_id=room.id)