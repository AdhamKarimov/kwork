from django.db import models
from django.utils import timezone
from django.conf import settings

from marketplace.models import Order


class ChatRoom(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='chat_rooms')
    client     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_rooms')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='freelancer_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('order', 'freelancer')

    def __str__(self):
        return f"{self.order.title} | {self.freelancer}"


class Message(models.Model):
    room       = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    content    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} - {self.content[:50]}"


class Offer(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'Kutilmoqda'
        ACCEPTED = 'ACCEPTED', 'Qabul qilindi'
        REJECTED = 'REJECTED', 'Rad etildi'
        EXPIRED  = 'EXPIRED',  "Muddati o'tgan"

    room           = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='offers')
    sender         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_offers')
    proposed_price = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_days  = models.PositiveIntegerField()
    message        = models.TextField(null=True, blank=True)
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at     = models.DateTimeField(auto_now_add=True)
    responded_at   = models.DateTimeField(null=True, blank=True)

    def accept(self):
        from datetime import timedelta
        self.status       = self.Status.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])

        order             = self.room.order
        order.status      = Order.Status.IN_PROGRESS
        order.final_price = self.proposed_price
        order.deadline    = timezone.now() + timedelta(days=self.delivery_days)
        order.save(update_fields=['status', 'final_price', 'deadline'])

        Offer.objects.filter(room=self.room, status=self.Status.PENDING).exclude(pk=self.pk).update(
            status=self.Status.EXPIRED
        )

    def reject(self):
        self.status       = self.Status.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])

    def __str__(self):
        return f"{self.proposed_price} so'm | {self.delivery_days} kun | {self.status}"