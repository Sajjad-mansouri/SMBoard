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
	create_board = models.BooleanField(default=False)
	edit_background = models.BooleanField(default=False)
	edit_board_title = models.BooleanField(default=False)
	edit_board_status = models.BooleanField(default=False)
	close_board = models.BooleanField(default=False)
	watch_board = models.BooleanField(default=False)
	unwatch_board = models.BooleanField(default=False)
	add_board_member = models.BooleanField(default=False)
	remove_board_member = models.BooleanField(default=False)
	create_list = models.BooleanField(default=False)
	edit_list_title = models.BooleanField(default=False)
	remove_list = models.BooleanField(default=False)
	archive_list = models.BooleanField(default=False)
	unarchive_list = models.BooleanField(default=False)
	change_lists_order = models.BooleanField(default=False)
	create_card = models.BooleanField(default=False)
	remove_card = models.BooleanField(default=False)
	edit_card_title = models.BooleanField(default=False)
	edit_card_description = models.BooleanField(default=False)
	edit_due_date = models.BooleanField(default=False)
	edit_start_date = models.BooleanField(default=False)
	edit_card_completed = models.BooleanField(default=False)
	set_card_cover = models.BooleanField(default=False)
	remove_card_cover = models.BooleanField(default=False)
	add_checklist = models.BooleanField(default=False)
	edit_checklist_name = models.BooleanField(default=False)
	remove_checklist = models.BooleanField(default=False)
	add_checklist_item = models.BooleanField(default=False)
	edit_checklist_item_name = models.BooleanField(default=False)
	edit_checklist_item_completed = models.BooleanField(default=False)
	remove_checklist_item = models.BooleanField(default=False)
	add_card_label = models.BooleanField(default=False)
	remove_card_label = models.BooleanField(default=False)
	archive_card = models.BooleanField(default=False)
	unarchive_card = models.BooleanField(default=False)
	add_attachment = models.BooleanField(default=False)
	remove_attachment = models.BooleanField(default=False)
	watch_card = models.BooleanField(default=False)
	unwatch_card = models.BooleanField(default=False)
	add_card_member = models.BooleanField(default=False)
	remove_card_member = models.BooleanField(default=False)
	copy_card = models.BooleanField(default=False)
	move_card = models.BooleanField(default=False)
	change_cards_order = models.BooleanField(default=False)
	add_comment = models.BooleanField(default=False)
	remove_comment = models.BooleanField(default=False)






	email_frequency = models.CharField(
		max_length=10, 
		choices=[
				("daily","Daily"),
				("weekly","Weekly"),
				("instantly", "Instantly"),
				("never", "Never")
			],
		default="instantly"

		)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


	def __str__(self):
		return f"Preferences for {self.user.email}"


class NotificationDelivery(models.Model):
	from board.models import Activity
	
	activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="activity_delivered_notifications")
	recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_delivered_notifications")

	created_at = models.DateTimeField(auto_now_add=True)

	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
					fields = ["activity", "recipient"],
					name="unique_notification_delivery"
				)
		]


class AboutMe(models.Model):
	bio = models.TextField()

class Connection(models.Model):
	title = models.CharField(max_length=150, help_text="github,linkedln,...")
	address = models.CharField(max_length=150)

class EmailInbox(models.Model):
	name = models.CharField(max_length=150)
	email = models.EmailField(max_length=150)
	message = models.TextField()


class AboutSite(models.Model):
	title = models.CharField(max_length=150, blank=True)
	api_endpoints = models.CharField(max_length=20,blank=True)
	data_models = models.CharField(max_length=20,blank=True)
	source_code_page = models.URLField()

class AboutSiteImage(models.Model):

	title = models.CharField(max_length=50, blank=True)
	slug = models.SlugField()
	img = models.ImageField(upload_to="about_site/")