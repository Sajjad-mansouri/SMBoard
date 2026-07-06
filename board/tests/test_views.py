import os
import shutil
import tempfile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth import get_user_model
from ..models import Board, BoardMembership
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
	@classmethod
	def setUpClass(cls):
		super().setUpClass()

		cls.temp_media = tempfile.mkdtemp()

		cls.override = override_settings(
			MEDIA_ROOT=cls.temp_media
		)
		cls.override.enable()

	@classmethod
	def tearDownClass(cls):
		cls.override.disable()
		shutil.rmtree(cls.temp_media)

		super().tearDownClass()
		
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

class SettingsViewTests(TestCase):
	def setUp(self):
		self.url = reverse("board:settings")
		self.user = User.objects.create_user(username="test_user", password="secure_pass_1234")

	def test_unauthenticated_user_is_redirected_to_login(self):
		response = self.client.get(self.url)
		login_url = reverse("account:login")
		expected_redirect_url = f"{login_url}?next={self.url}"
		self.assertRedirects(response, expected_redirect_url, status_code=302)

	def test_authenticated_user_can_access_settings(self):
		self.client.login(username="test_user", password="secure_pass_1234")
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "board/setting/settings.html")

class BoardDetailViewTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username="owner", email="owner@email.com",password="secure_pass_1234")
		self.member = User.objects.create_user(username="member", email="member@email.com",password="secure_pass_1234")
		self.stranger = User.objects.create_user(username="stranger", email="stranger@email.com",password="secure_pass_1234")
		self.board = Board.objects.create(owner=self.owner, name="Project")
		BoardMembership.objects.create(user=self.member, board=self.board)
		self.url = reverse("board:board_detail", kwargs={"pk":self.board.id})

	def test_unauthenticated_user_cannot_access_board(self):
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 302)

	def test_owner_can_access_board(self):
		self.client.login(username="owner", password="secure_pass_1234")
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "board/board/main.html")

	def test_member_can_access_board(self):
		self.client.login(username="member", password="secure_pass_1234")
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "board/board/main.html")

	def test_can_not_access_closed_board(self):
		self.board.closed = True
		self.board.save()
		self.client.login(username="owner", password="secure_pass_1234")
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 404)

class PublicBoardDetailViewTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username="owner", password="secure_pass_1234")

		self.public_board = Board.objects.create(
				owner=self.owner,
				name="public project",
				slug="public-project-board",
				short_uuid = "a1b2c3d4",
				status="public"

			)


		self.private_board = Board.objects.create(
				owner=self.owner,
				name="private project",
				slug="private-project-board",
				short_uuid = "e5f6g7h8",
				status="private"

			)

		self.url_name = "board:public_board_detail"

	def test_anonymous_user_can_access_public_board(self):
		url = reverse(
				self.url_name,
				kwargs={
				"short_uuid":self.public_board.short_uuid,
				"slug":self.public_board.slug
				}
			)
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "board/board/public.html")

	def test_cannot_access_private_board_via_public_view(self):
		url = reverse(
				self.url_name,
				kwargs={
				"short_uuid":self.private_board.short_uuid,
				"slug":self.private_board.slug
				}
			)
		response = self.client.get(url)
		self.assertEqual(response.status_code, 404)

	def test_mismatch_slug(self):

		url = reverse(
				self.url_name,
				kwargs={
				"short_uuid":self.public_board.short_uuid,
				"slug":"malicious-altered-slug-text"
				}
			)
		response = self.client.get(url)
		self.assertEqual(response.status_code, 404)

	def test_mismatch_short_uuid(self):

		url = reverse(
				self.url_name,
				kwargs={
				"short_uuid":"wrong123",
				"slug":self.public_board.slug
				}
			)
		response = self.client.get(url)
		self.assertEqual(response.status_code, 404)