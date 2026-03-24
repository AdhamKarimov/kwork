from django import template
from notifications.models import Notification

register = template.Library()


@register.simple_tag
def get_unread_notifications(user):
    """O'qilmagan oxirgi 10 ta bildirishnoma."""
    return Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:10]


@register.simple_tag
def get_unread_count(user):
    """O'qilmagan bildirishnomalar soni."""
    return Notification.objects.filter(user=user, is_read=False).count()