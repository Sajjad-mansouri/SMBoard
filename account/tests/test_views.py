import json
from unittest.mock import patch, Mock
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.core import mail
from account.views import RegistrationView,RegistrationDoneView

User = get_user_model()

class RegistrationViewTests(TestCase):

	def setUp(self):
		self.factory = RequestFactory()
		self.url = reverse("account:register")
		self.valid_data = {
			'username': "testuser",
			'email': "test@example.com",
			'password1': "TestPassword123!",
			'password2': "TestPassword123!",

		}

	def test_user_registration_view_url_exists(self):
		"""Test that registration view is accessible"""
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 200)

	def test_registeration_view_template_used(self):
		response = self.client.get(self.url)
		self.assertTemplateUsed(response, "account/registration/register.html")

	def test_registeration_view_context(self):
		response = self.client.get(self.url)
		self.assertIn("form", response.context)


	def test_registeration_form_valid_json_response(self):
		response = self.client.post(
			self.url,
			data=self.valid_data,
			HTTP_ACCEPT="application/json"
			)

		self.assertEqual(response.status_code, 200)
		self.assertIsInstance(response, JsonResponse)
		content = json.loads(response.content)
		self.assertIn("status", content)

		self.assertTrue(User.objects.filter(username="testuser").exists())
		user = User.objects.get(username="testuser")
		self.assertEqual(user.email, "test@example.com")

		self.assertEqual(self.client.session["email"], "test@example.com")

	def test_registration_form_invalid_json_response(self):
		invalid_data = {
			'username': 'testuser',
			'email': 'invalid-email',  # Invalid email
			'password1': 'password123',
			'password2': 'password456',  # Passwords don't match
		}

		response = self.client.post(
			self.url,
			data=invalid_data,
			HTTP_ACCEPT="application/json"
			)
		self.assertEqual(response.status_code, 200)
		self.assertIsInstance(response, JsonResponse)

		content = json.loads(response.content)
		self.assertIn("errors", content)
		self.assertFalse(content["status"])
		self.assertIsInstance(content["errors"], dict)


	def test_registeration_form_valid_non_json_response(self):
		with patch.object(RegistrationView, "response_type", "html"):
			response = self.client.post(
				self.url,
				data=self.valid_data,
				)


			self.assertRedirects(response, reverse("account:registration_done"))
			self.assertTrue(User.objects.filter(username="testuser").exists())

	def test_registeration_form_invalid_non_json_response(self):
		invalid_data = {
			'username': 'testuser',
			'email': 'invalid-email',  # Invalid email
			'password1': 'password123',
			'password2': 'password456',  # Passwords don't match
		}
		with patch.object(RegistrationView, "response_type", "html"):
			response = self.client.post(
				self.url,
				data=invalid_data,
				)


			self.assertEqual(response.status_code, 200)
			self.assertTemplateUsed(response, "account/registration/register.html")
			self.assertTrue(response.context["form"].errors)

	def test_registration_form_send_email(self):
		response = self.client.post(
			self.url,
			data=self.valid_data,
			HTTP_ACCEPT="application/json"
			)

		# Check that one email was sent
		self.assertEqual(len(mail.outbox), 1)

		#check email content
		email = mail.outbox[0]
		self.assertIn("test@example.com", email.to)
		self.assertIn("You're receiving this email because you created an account", email.body)

		# Check that user is inactive until confirmed
		user = User.objects.get(username="testuser")
		self.assertFalse(user.is_active)


	def test_registration_form_email_template_used(self):
		"""Test that correct email templates are used"""
		with patch.object(RegistrationView, "html_email_template_name", "account/registration/registration_email.txt"),\
		patch("account.views.RegistrationView.subject_template_name", "account/registration/registration_subject.txt"):
			response = self.client.post(
				self.url,
				data=self.valid_data,
				HTTP_ACCEPT="application/json"
				)

			self.assertEqual(len(mail.outbox), 1)

	def test_registration_view_extra_email_context(self):
		extra_email_context = {
			"test_context": "value"
		}
		with patch.object(RegistrationView, "extra_email_context", extra_email_context):
			with patch("account.forms.UserRegistrationForm.save") as mock_save:
				response = self.client.post(
					self.url,
					data=self.valid_data,
					HTTP_ACCEPT="application/json"
					)
				# Check that extra_email_context was passed to form.save
				call_args = mock_save.call_args[1]
				self.assertEqual(call_args["extra_email_context"] ,extra_email_context)

	def test_registeration_view_token_generator(self):
		custome_token = Mock()
		with patch.object(RegistrationView, "token_generator", custome_token):
			with patch("account.forms.UserRegistrationForm.save") as mock_save:
				self.client.post(self.url, data=self.valid_data)
				call_args = mock_save.call_args[1]
				self.assertEqual(call_args["token_generator"], custome_token)

	def test_registration_view_from_email(self):
		cusom_from_email = "custom@email.com"
		with patch.object(RegistrationView, "from_email", cusom_from_email):
			with patch("account.forms.UserRegistrationForm.save") as mock_save:
				self.client.post(self.url, data=self.valid_data)
				call_args = mock_save.call_args[1]
				self.assertEqual(call_args["from_email"], cusom_from_email)

	def test_registration_view_https_enabled(self):
		"""Test HTTPS option is passed correctly when request is secure"""

		request = self.factory.post(self.url, data=self.valid_data)
		request.is_secure = Mock(return_value=True)
		request.session = {}
		with patch("account.forms.UserRegistrationForm.save") as mock_save:
			view = RegistrationView()
			view.request = request
			form = view.form_class(data=self.valid_data)
			form.is_valid()
			view.form_valid(form)
			call_args = mock_save.call_args[1]
			self.assertTrue(call_args["use_https"])

	def test_registration_view_https_disabled(self):
		request = self.factory.post(self.url, data=self.valid_data)
		request.is_secure = Mock(return_value=False)
		request.session = {}
		with patch("account.forms.UserRegistrationForm.save") as mock_save:
			view = RegistrationView()
			view.request = request
			form = view.form_class(data=self.valid_data)
			form.is_valid()
			view.form_valid(form)
			call_args = mock_save.call_args[1]
			self.assertFalse(call_args["use_https"])

	def test_registration_form_preserves_session_email(self):
		"""Test that email is stored in session after successful registration"""
		response = self.client.post(self.url, data=self.valid_data)
		
		session = self.client.session
		self.assertEqual(session["email"], "test@example.com")

	def test_registration_form_duplicate_username(self):
		"""Test registration with duplicate username"""
		# First create a user
		User.objects.create_user(
			username="testuser",
			email="existing@example.com",
			password="TestPassword123!"
		)
		
		# Try to register with same username
		response = self.client.post(
			self.url,
			data=self.valid_data,
			HTTP_ACCEPT="application/json"
		)
		
		content = json.loads(response.content)
		self.assertFalse(content["status"])
		self.assertIn("username", content["errors"])

	def test_registration_form_duplicate_email(self):
		"""Test registration with duplicate username"""
		# First create a user
		User.objects.create_user(
			username="test_user",
			email="test@example.com",
			password="TestPassword123!"
		)
		
		# Try to register with same username
		response = self.client.post(
			self.url,
			data=self.valid_data,
			HTTP_ACCEPT="application/json"
		)
		
		content = json.loads(response.content)
		self.assertFalse(content['status'])
		self.assertIn("email", content["errors"])

	def test_registration_form_password_too_short(self):
		"""Test registration with password that's too short"""
		invalid_data = self.valid_data.copy()
		invalid_data["password1"] = "short"
		invalid_data["password2"] = "short"
		
		response = self.client.post(
			self.url,
			data=invalid_data,
			HTTP_ACCEPT="application/json"
		)
		
		content = json.loads(response.content)
		self.assertFalse(content["status"])
		
		# Check that user was not created
		self.assertEqual(User.objects.count(), 0)

class RegistrationDoneViewTests(TestCase):
	def setUp(self):

		self.url = reverse("account:registration_done")
		self.valid_email = "example@email.com"

	def test_registeration_view_done_url_exists(self):
		"""Test that the view is accessible"""
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 200)

	def test_registration_view_done_template_used(self):
		"""Test that correct template is used"""
		response = self.client.get(self.url)
		self.assertTemplateUsed(response, "account/registration/registration_done.html")

	def test_registration_done_view_context_contains_title(self):
		"""Test that context contains the title"""
		custome_title = "custome_title"
		with patch("account.views.RegistrationDoneView.title",custome_title):
			response = self.client.get(self.url)

			self.assertIn("title", response.context)
			self.assertEqual(response.context["title"], custome_title)

	def test_registration_done_view_title_is_set(self):
		"""Test that title attribute is set correctly"""
		response = self.client.get(self.url)
		self.assertEqual(response.context["title"], _("Activition Email sent"))

	def test_registration_done_view_email_from_session(self):
		"""Test that email is retrieved from session correctly"""
		session = self.client.session
		session["email"] = self.valid_email
		session.save()

		response = self.client.get(self.url)

		self.assertEqual(response.context["email"], self.client.session["email"])

	def test_registration_done_view_no_email_in_session(self):
		"""Test that context returns None when email not in session"""
		session = self.client.session
		session.flush()

		response = self.client.get(self.url)

		self.assertIn('email', response.context)
		self.assertIsNone(response.context["email"])

	def test_registration_done_view_inherits_from_templateview(self):
		"""Test that view properly inherits from TemplateView"""
		from django.views.generic.base import TemplateView
		self.assertTrue(issubclass(RegistrationDoneView, TemplateView))