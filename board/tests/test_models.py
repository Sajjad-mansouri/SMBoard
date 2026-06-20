import os
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import (
					Board, 
					board_image_path,#function
					BoardList,
					list_cover_path,#function
					)


User = get_user_model()

class BoardModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="sajjad", password="secure_pass_1234")

	def test_string_representation(self):
		"""Ensure __str__ formats user ownership and board name correctly."""
		board = Board.objects.create(owner=self.user, name="My Project")
		expected_string = f"{self.user} board: My Project"
		self.assertEqual(str(board), expected_string)

	def test_sluggify_on_save(self):
		"""Ensure the save override automatically generates a slug from the name."""
		board_name = "My Trello Like Project"
		board = Board.objects.create(owner=self.user, name=board_name)
		self.assertTrue(board.slug)
		self.assertEqual(board.slug,slugify(board_name))

	def test_short_uuid_generation(self):
		"""Ensure every board is initialized with a distinct 6-character short UUID."""
		board_one = Board.objects.create(owner=self.user, name="Board One")
		board_two = Board.objects.create(owner=self.user, name="Board Two")

		self.assertEqual(len(board_one.short_uuid), 6)
		self.assertNotEqual(board_one.short_uuid, board_two.short_uuid)

	def test_board_image_path_resolution(self):
		"""Verify the uploaded_to callable creates the exact expected multi-tier path"""

		board = Board.objects.create(owner=self.user, name="My Project")
		now = timezone.now()
		file_name = "background.jpg"
		generated_path = board_image_path(board, file_name)

		expected_path = f"{self.user.id}/My Project/board_files/{now.year}/{now.month}/{now.day}/{file_name}"

		self.assertEqual(generated_path, expected_path)


	def test_file_upload_retain_correct_path_in_db(self):

		dummy_image = SimpleUploadedFile(
			name="test_bg.png",
			content=b'\x47\x49\x46',
			content_type="image/png"
			)

		board = Board.objects.create(owner=self.user, name="My Project", background_image=dummy_image)
		now = timezone.now()
		expected_path = f"{self.user.id}/My Project/board_files/{now.year}/{now.month}/{now.day}/test_bg.png"

		self.assertEqual(board.background_image.name, expected_path)

		if board.background_image and os.path.exists(board.background_image.path):
			os.remove(board.background_image.path)

class BoardListModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="sajjad", password="secure_pass_1234")
		self.board = Board.objects.create(owner=self.user, name="Project")

	def test_string_representation(self):
		board_list = BoardList.objects.create(board=self.board, name="In Progress")
		expected_string = f"In Progress is list of  {self.user} {self.board} board "
		self.assertEqual(str(board_list), expected_string)


	def test_list_cover_path_resolution(self):
		"""Verify the list_cover_path callable creates the exact expected multi-tier path"""

		board_list = BoardList.objects.create(board=self.board, name="In Progress")
		now = timezone.now()
		file_name = "background.jpg"
		generated_path = list_cover_path(board_list, file_name)

		expected_path = f"{self.user.id}/{self.board.name}/list_files/In Progress/{now.year}/{now.month}/{now.day}/{file_name}"

		self.assertEqual(generated_path, expected_path)

	def test_default_ordering_meta(self):
		list2 = BoardList.objects.create(board=self.board, name="list2", order=2)
		list1 = BoardList.objects.create(board=self.board, name="list1", order=1)
		list3 = BoardList.objects.create(board=self.board, name="list3", order=3)

		board_lists = list(BoardList.objects.filter(board=self.board))
		self.assertEqual(board_lists[0], list1)
		self.assertEqual(board_lists[1], list2)
		self.assertEqual(board_lists[2], list3)

	def test_file_upload_retain_correct_path_in_db(self):

		dummy_image = SimpleUploadedFile(
			name="test_bg.png",
			content=b'\x47\x49\x46',
			content_type="image/png"
			)

		board_list = BoardList.objects.create(board=self.board, name="In Progress", cover_image=dummy_image)
		now = timezone.now()
		expected_path = f"{self.user.id}/{self.board.name}/list_files/In Progress/{now.year}/{now.month}/{now.day}/test_bg.png"

		self.assertEqual(board_list.cover_image.name, expected_path)

		if board_list.cover_image and os.path.exists(board_list.cover_image.path):
			os.remove(board_list.cover_image.path)