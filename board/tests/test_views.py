import os
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth import get_user_model

from account.models import AboutSiteImage, Connection, AboutSite

User = get_user_model()

class HomePageViewTests(TestCase):
	def setUp(self):
		"""Define the target URL and construct a mock user instance"""
		self.url = reverse("board:home")
		self.user = User.objects.create_user(username="test_user", password="secure_pass_1234")

	def test_anonymous_user_redirect_to_landing(self):
		"""Ensure unauthenticated guests are forced onto the landing screen via 302 redirect"""

		response = self.client.get(self.url)

		expected_redirect_url = reverse("board:landing")
		self.assertRedirects(response, expected_redirect_url, status_code=302)

	def test_authenticated_user_can_access_home_page(self):
		"""Ensure logged-in accounts can access the dashboard workspace with a 200 status."""

		self.client.login(username="test_user", password="secure_pass_1234")
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "board/home/home.html")

class LandingPageViewTests(TestCase):

	def setUp(self):
		self.url = reverse("board:landing")


	def test_landing_page_renders_successfully_when_db_is_empty(self):
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "board/landing/landing.html")


		self.assertNotIn("dashboard_img_url", response.context)
		self.assertNotIn("github", response.context)

	def test_landing_page_populate_context_when_data_exists(self):
		"""ensure context dictionary contains correct model urls and strings when available"""

		dummy_image = SimpleUploadedFile(name="file.png",content=b'pixels')
		image_titles = [
			"dashboard", "setting_notif", "board_menu", "board_activity", "card", "member_management"
		]

		site_images = []
		for title in image_titles:
			dummy_image = SimpleUploadedFile(name=f"{title}_file_random.png",content=b'pixels')

			site_image = AboutSiteImage.objects.create(title=title, img=dummy_image)
			site_images.append(site_image)

		connections = {
			"github": "https://github.com/profile",
			"linkedln": "https://linkedin.com/in/profile",
			"email": "mailto:dev@example.com",
			"telegram": "https://t.me/profile"
		}

		connection_objs = []
		for title, address in connections.items():
			connection_objs.append(Connection(title=title, address=address)) 	
		Connection.objects.bulk_create(connection_objs)


		AboutSite.objects.create(source_code_page="https://github.com/repo")


		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 200)


		self.assertEqual(response.context["dashboard_img_url"], "/media/about_site/dashboard_file_random.png")
		self.assertEqual(response.context["github"], "https://github.com/profile")
		self.assertEqual(response.context["telegram"], "https://t.me/profile")
		self.assertEqual(response.context["source_code_url"], "https://github.com/repo")

		for site_image in site_images:
			if site_image.img and os.path.exists(site_image.img.path):
				os.remove(site_image.img.path)