from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT     = 'CLIENT',     'Mijoz'
        FREELANCER = 'FREELANCER', 'Frilanser'

    email     = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role      = models.CharField(max_length=20, choices=Role.choices)
    avatar    = models.ImageField(upload_to='avatars/', null=True, blank=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'full_name', 'role']

    def __str__(self):
        return self.full_name


class Profile(models.Model):
    class Level(models.IntegerChoices):
        BEGINNER = 1, 'Boshlovchi'
        MIDDLE   = 2, "O'rta"
        EXPERT   = 3, 'Ekspert'

    user                 = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio                  = models.TextField(null=True, blank=True)
    skills               = models.JSONField(default=list, blank=True)
    level                = models.IntegerField(choices=Level.choices, default=Level.BEGINNER)
    rating               = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    completed_jobs_count = models.PositiveIntegerField(default=0)

    def update_level(self):
        if self.completed_jobs_count >= 20:
            self.level = self.Level.EXPERT
        elif self.completed_jobs_count >= 5 and self.rating >= 4.5:
            self.level = self.Level.MIDDLE
        else:
            self.level = self.Level.BEGINNER
        self.save(update_fields=['level'])

    def __str__(self):
        return f"{self.user.full_name} - Level {self.level}"


class Emailcode(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='emailcode')
    code =models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_activated = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True,blank=True)

    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def save(self, *args , **kwargs ):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super(Emailcode,self).save(*args, **kwargs)