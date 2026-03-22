from django.shortcuts import render, redirect
from django.views import View
from .models import Notification

class NotificationListView(View):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        return render(request, 'notifications/list.html', {'notifications': notifications})

class MarkAsReadView(View):
    def post(self, request, pk):
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('notifications:list')