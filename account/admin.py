from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from .models import User, Profile, Notification, NotificationDelivery

@admin.register(User)
class UserAdmin(UserAdmin):
	list_display = ["id", *UserAdmin.list_display]
	ordering = ("-date_joined", )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ["get_profile_image", "bio"]


	def get_profile_image(self, obj):
		return mark_safe(f"<img src='{obj.get_image()}' width='50'>")


@admin.register(Notification)
class UserAdmin(admin.ModelAdmin):
	list_display = ["id", "user", "email_frequency"]


@admin.register(NotificationDelivery)
class UserAdmin(admin.ModelAdmin):
	list_display = ["id", "Activity", "recipient"]