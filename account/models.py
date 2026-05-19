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
