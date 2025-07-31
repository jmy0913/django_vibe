from django.contrib import admin

# Register your models here.

from .models import Custom_user, Nickname

admin.site.register(Custom_user)
admin.site.register(Nickname)
