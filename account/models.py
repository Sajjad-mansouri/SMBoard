from django.db import models
from django.db.models import UniqueConstraint, Q
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
	email = models.EmailField(_("Email Address"), blank=True, unique=True)

	REQUIRED_FIELDS = ["email"]


	def get_display_name(self):
		if self.first_name or self.last_name:
			return self.get_full_name()
		else:
			return self.username

class Profile(models.Model):

	user = models.OneToOneField(User, on_delete=models.CASCADE ,verbose_name=_("User"))
	profile_image = models.ImageField(_("Profile Image"), upload_to="users", null=True,blank=True)
	bio = models.CharField(_("Bio"), max_length=200, blank=True)
	
	def __str__(self):
		return f'{self.user.username}-"{self.user.get_full_name()}" profile'


	class Meta:
		verbose_name = _("Profile")
		verbose_name_plural = _("Profiles")

	def get_image(self):
		if self.profile_image:
			return self.profile_image.url
		else:
			return ""



class Notification(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)

	#email on 
	board_background_edited = models.BooleanField(default=False)
	board_title_edited = models.BooleanField(default=False)
	board_status_edited = models.BooleanField(default=False)
	board_closed = models.BooleanField(default=False)


	list_created = models.BooleanField(default=False)
	list_title_edited = models.BooleanField(default=False)
	list_removed = models.BooleanField(default=False)
	list_archived = models.BooleanField(default=False)
	list_order_changed = models.BooleanField(default=False)


	card_created = models.BooleanField(default=False)
	card_title_edited = models.BooleanField(default=False)
	card_completed_edited = models.BooleanField(default=False)
	card_archived = models.BooleanField(default=False)
	card_description_edited = models.BooleanField(default=False)
	card_due_date_edited = models.BooleanField(default=False)
	card_start_date_edited = models.BooleanField(default=False)
	card_cover_set = models.BooleanField(default=False)
	card_cover_removed = models.BooleanField(default=False)
	checklist_added = models.BooleanField(default=False)
	checklist_removed = models.BooleanField(default=False)
	checklist_item_added = models.BooleanField(default=False)
	checklist_item_edited_completed = models.BooleanField(default=False)
	checklist_item_removed = models.BooleanField(default=False)
	label_added = models.BooleanField(default=False)
	label_removed = models.BooleanField(default=False)
	attachment_added = models.BooleanField(default=False)
	card_order_changed = models.BooleanField(default=False)
	comment_added = models.BooleanField(default=False)



	email_frequency = models.CharField(
		max_length=10, 
		choices=[
				("daily","Daily"),
				("weekly","Weekly"),
				("instantly", "Instantly")
			],
		default="instantly"

		)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


	def __str__(self):
		return f"Preferences for {self.user.email}"


class NotificationDelivery(models.Model):
	from board.models import Activity
	
	Activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="activity_delivered_notifications")
	recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_delivered_notifications")

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
