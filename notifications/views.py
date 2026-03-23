
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from .models import Notification


class NotificationListView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        unread_count = notifications.filter(is_read=False).count()
        # Sahifaga kirganda hammasini o'qilgan deb belgilash
        notifications.filter(is_read=False).update(is_read=True)
        context = {
            'notifications': notifications,
            'unread_count': unread_count,
        }
        return render(request, 'notifications/list.html', context)


class MarkAsReadView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
        return redirect('notifications:list')


class MarkAllReadView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
        return redirect('notifications:list')


class UnreadCountView(LoginRequiredMixin, View):
    """Navbar uchun o'qilmagan bildirishnomalar soni (AJAX)."""

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'count': count})
