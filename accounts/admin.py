from django.contrib import admin
from .models import Profile,User,Emailcode
# Register your models here.
admin.site.register([Profile,User,Emailcode])