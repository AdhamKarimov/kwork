from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order
from django.db.models import Case, When, Value, IntegerField

class OrderListView(View):
    """
    TZ C-bandi: Daraja baland bo'lsa, e'lonlar yuqorida ko'rinadi.
    Biz bu yerda frilanserni emas, mijozning e'lonini ko'rsatamiz, 
    lekin buyurtmalarni yaratilgan vaqti bo'yicha saralaymiz.
    """
    def get(self, request):
        orders = Order.objects.filter(status=Order.Status.OPEN).order_by('-created_at')
        return render(request, 'marketplace/order_list.html', {'orders': orders})

class OrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'CLIENT':
            return redirect('marketplace:order_list')
        return render(request, 'marketplace/order_create.html')

    def post(self, request):
        title = request.POST.get('title')
        description = request.POST.get('description')
        budget = request.POST.get('budget')
        
        Order.objects.create(
            client=request.user,
            title=title,
            description=description,
            initial_budget=budget,
            status=Order.Status.OPEN
        )
        return redirect('marketplace:order_list')

class OrderDetailView(View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return render(request, 'marketplace/order_detail.html', {'order': order})