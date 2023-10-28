from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribers, Users


@admin.register(Users)
class UserAdmin(UserAdmin):
    list_display = (
        "is_active",
        "username",
        "first_name",
        "last_name",
        "email",
    )
    list_filter = (
        "is_active",
        "first_name",
        "email",
    )


@admin.register(Subscribers)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )
