from django.shortcuts import redirect, get_object_or_404, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Review
from marketplace.models import Order


class CreateReviewView(LoginRequiredMixin, View):
    """
    TZ C-bandi: Ish topshirilgach sharh berish va level yangilash.
    Faqat mijoz, faqat COMPLETED buyurtma uchun, faqat bir marta.
    """

    def post(self, request, order_id):
        order = get_object_or_404(
            Order.objects.select_related('client'),
            id=order_id,
        )

        # Faqat shu buyurtmaning mijozi sharh yoza oladi
        if request.user != order.client:
            raise PermissionDenied('Faqat buyurtma egasi sharh yoza oladi.')

        # Faqat yakunlangan buyurtmaga sharh yoziladi
        if order.status != Order.Status.COMPLETED:
            return redirect('marketplace:order_detail', pk=order_id)

        # Takroriy sharh tekshiruvi — bir buyurtmaga bir marta
        if Review.objects.filter(order=order, reviewer=request.user).exists():
            return redirect('marketplace:order_detail', pk=order_id)

        # Qabul qilingan taklifni topish
        chat_room = order.chat_rooms.first()
        if not chat_room:
            return redirect('marketplace:order_detail', pk=order_id)

        accepted_offer = chat_room.offers.filter(status='ACCEPTED').first()
        if not accepted_offer:
            return redirect('marketplace:order_detail', pk=order_id)

        # Stars validatsiyasi (1–5)
        try:
            stars = int(request.POST.get('stars', 0))
            if stars < 1 or stars > 5:
                raise ValueError
        except (ValueError, TypeError):
            return render(request, 'marketplace/order_detail.html', {
                'order': order,
                'error': 'Baho 1 dan 5 gacha bo\'lishi kerak.',
            })

        comment = request.POST.get('comment', '').strip()

        Review.objects.create(
            order      = order,
            reviewer   = request.user,
            freelancer = accepted_offer.sender,
            stars      = stars,
            comment    = comment,
        )
        # Review modelidagi save() → _update_freelancer_rating()
        # avtomatik ravishda Profilning levelini yangilaydi.

        return redirect('marketplace:order_detail', pk=order_id)