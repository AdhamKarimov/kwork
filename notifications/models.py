from django.db import models
from django.conf import settings

# Create your models here.
class Notification(models.Model):
    class Type(models.TextChoices):
        OFFER_RECEIVED  = 'OFFER_RECEIVED',  'Yangi taklif keldi'
        OFFER_ACCEPTED  = 'OFFER_ACCEPTED',  'Taklif qabul qilindi'
        OFFER_REJECTED  = 'OFFER_REJECTED',  'Taklif rad etildi'
        DEADLINE_SOON   = 'DEADLINE_SOON',   'Muddat yaqinlashmoqda'
        DEADLINE_PASSED = 'DEADLINE_PASSED', 'Muddat o\'tdi'
        ORDER_COMPLETED = 'ORDER_COMPLETED', 'Ish tugatildi'
        MESSAGE         = 'MESSAGE',         'Yangi xabar'


    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=Type.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} → {self.user.full_name}"