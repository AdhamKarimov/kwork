from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Review
from marketplace.models import Order

class CreateReviewView(LoginRequiredMixin, View):
    """TZ C-bandi: Ish topshirilgach sharh berish va level yangilash"""
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        
        if request.user == order.client and order.status == Order.Status.COMPLETED:
            # Qabul qilingan taklif egasini (frilanserni) topamiz
            accepted_offer = order.chat_rooms.first().offers.filter(status='ACCEPTED').first()
            
            Review.objects.create(
                order=order,
                reviewer=request.user,
                freelancer=accepted_offer.sender,
                stars=request.POST.get('stars'),
                comment=request.POST.get('comment')
            )
            # Review modelidagi save() va _update_freelancer_rating() 
            # avtomatik ravishda Profilning levelini yangilaydi.
        return redirect('marketplace:order_detail', pk=order_id)