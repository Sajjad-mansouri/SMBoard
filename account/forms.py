from django.template import loader
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import _unicode_ci_compare
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


UserModel = get_user_model()
class UserRegistrationForm(UserCreationForm):

	class Meta:
		model = UserModel
		fields = ("first_name", "last_name", "email")


	def send_mail(
		self,
		subject_template_name,
		email_template_name,
		context,
		from_email,
		to_email,
		html_email_template_name=None,
	):
		"""
		Send a django.core.mail.EmailMultiAlternatives to `to_email`.
		"""
		subject = loader.render_to_string(subject_template_name, context)
		# Email subject *must not* contain newlines
		subject = "".join(subject.splitlines())
		body = loader.render_to_string(email_template_name, context)

		email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
		if html_email_template_name is not None:
			html_email = loader.render_to_string(html_email_template_name, context)
			email_message.attach_alternative(html_email, "text/html")

		try:
			email_message.send(fail_silently=False)
		except Exception:
			# logger.exception(
			# 	"Failed to send password reset email to %s", context["user"].pk
			# )
			pass

	def get_users(self, email):
		"""Given an email, return matching user(s) who should receive a reset.

		This allows subclasses to more easily customize the default policies
		that prevent inactive users and users with unusable passwords from
		resetting their password.
		"""
		email_field_name = UserModel.get_email_field_name()
		active_users = UserModel._default_manager.filter(
			**{
				"%s__iexact" % email_field_name: email,
				# "is_active": True,
			}
		)
		return (
			u
			for u in active_users
			if u.has_usable_password()
			and _unicode_ci_compare(email, getattr(u, email_field_name))
		)

	def _save(
		self,
		domain_override=None,
		subject_template_name="account/registration/registration_subject.txt",
		email_template_name="account/registration/registration_email.html",
		use_https=False,
		token_generator=default_token_generator,
		from_email=None,
		request=None,
		html_email_template_name=None,
		extra_email_context=None,
	):
		"""
		Generate a one-use only link for resetting password and send it to the
		user.
		"""


		email = self.cleaned_data["email"]
		if not domain_override:
			current_site = get_current_site(request)
			site_name = current_site.name
			domain = current_site.domain
		else:
			site_name = domain = domain_override
		email_field_name = UserModel.get_email_field_name()

		for user in self.get_users(email):
			user_email = getattr(user, email_field_name)
			user_pk_bytes = force_bytes(UserModel._meta.pk.value_to_string(user))
			
			context = {
				"email": user_email,
				"domain": domain,
				"site_name": site_name,
				"uid": urlsafe_base64_encode(user_pk_bytes),
				"user": user,
				"token": token_generator.make_token(user),
				"protocol": "https" if use_https else "http",
				**(extra_email_context or {}),
			}
			
			self.send_mail(
				subject_template_name,
				email_template_name,
				context,
				from_email,
				user_email,
				html_email_template_name=html_email_template_name,
			)
	def save(self, commit=True, **opts):
		
		user = super().save(commit=False)
		user.is_active = False
		user.save()
		
		self._save(**opts)
		return user

