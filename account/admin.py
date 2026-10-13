from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import (
    AboutMe,
    AboutSite,
    AboutSiteImage,
    Connection,
    EmailInbox,
    Notification,
    NotificationDelivery,
    Profile,
    User,
)


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ["id", *UserAdmin.list_display]
    ordering = ("-date_joined",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["get_profile_image", "bio"]

    def get_profile_image(self, obj):
        return mark_safe(f"<img src='{obj.get_image()}' width='50'>")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "email_frequency"]


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ["id", "activity", "recipient"]


@admin.register(AboutMe)
class AboutMeAdmin(admin.ModelAdmin):
    list_display = ["id", "bio"]


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ["title", "address"]


@admin.register(EmailInbox)
class EmailInboxAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "email"]


@admin.register(AboutSite)
class AboutSiteAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "source_code_page"]


@admin.register(AboutSiteImage)
class AboutSiteImageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
    ]
