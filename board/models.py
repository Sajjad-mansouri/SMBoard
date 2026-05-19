from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

UserModel = get_user_model()

def board_image_path(instance, file_name):
	return "{user}/{board}/{year}/{month}/{day}/{file_name}".format(
										user=instance.user_id,
										board=instance.name, 
										year = instance.updated.year,
										month = instance.updated.month,
										day = instance.updated.day,
										file_name = file_name)

class Board(models.Model):
	STATUS_CHOICES = [
	("private", "Private"),
	("workspace", "Workspace"),
	("public", "Public")
	]
	user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"), related_name="user_boards")
	name = models.CharField(_("Name"), max_length=250)
	status = models.CharField(_("Status"), choices=STATUS_CHOICES, max_length=10)
	background_color = models.CharField(_("Background Color"), max_length=7, help_text="format:#00fca8", blank=True)
	background_image = models.ImageField(_("Background Image"), upload_to=board_image_path, null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)


	def __str__(self):
		return f"{self.user} board: {self.name}"

	class Meta:
		verbose_name = _("Board")
		verbose_name_plural = _("Boards")


class BoardMembership(models.Model):
	MEMBER_TYPES = [
		("admin", "Admin"),
		("member", "Member"),
		("observer", "Observer"),
		("guest", "Guest")
	]
	user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"), related_name="user_memberships")
	board = models.ForeignKey(Board, on_delete=models.CASCADE, verbose_name=_("Board"), related_name="board_memberships")
	member_type = models.CharField(_("Member Type"), choices=MEMBER_TYPES, max_length=8)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.user} is {self.board} board {self.member_type} member"

	class Meta:
		verbose_name = _("Board Member")
		verbose_name_plural = _("Boards Members")