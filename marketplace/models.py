from django.db import models
from django.conf import settings


class Order(models.Model):
    class Status(models.TextChoices):
        OPEN           = 'OPEN',           'Ochiq'
        IN_NEGOTIATION = 'IN_NEGOTIATION', 'Kelishilmoqda'
        IN_PROGRESS    = 'IN_PROGRESS',    'Jarayonda'
        COMPLETED      = 'COMPLETED',      'Tugatilgan'
        DELAYED        = 'DELAYED',        'Kechikkan'
        CANCELLED      = 'CANCELLED',      'Bekor qilingan'

    client         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    title          = models.CharField(max_length=255)
    description    = models.TextField()
    initial_budget = models.DecimalField(max_digits=12, decimal_places=2)
    final_price    = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    deadline       = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.status}] {self.title}"