import os
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import (
					Board, 
					board_image_path,#function
					BoardList,
					list_cover_path,#function
					Card,
					card_cover_path,#function
					BoardMembership,
					CardMembership,
					CardLabel,
					CheckList,
					ChecklistItem
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

class CardModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="sajjad", password="secure_pass_1234")
		self.board = Board.objects.create(owner=self.user, name="Project")
		self.board_list = BoardList.objects.create(board=self.board, name="In Progress")


	def test_string_representation(self):
		card = Card.objects.create(board_list=self.board_list, name="card1")
		expected_string = f"card1 is card of  {self.board_list} list"
		self.assertEqual(str(card), expected_string)


	def test_card_cover_path_resolution(self):
		"""Verify the card_cover_path callable creates the exact expected multi-tier path"""

		card = Card.objects.create(board_list=self.board_list, name="card1")
		now = timezone.now()
		file_name = "cover.jpg"
		generated_path = card_cover_path(card, file_name)

		expected_path = f"{self.user.id}/{self.board.name}/{self.board_list.name}/card1/card_cover/{now.year}/{now.month}/{now.day}/{file_name}"

		self.assertEqual(generated_path, expected_path)

	def test_default_ordering_meta(self):
		card2 = Card.objects.create(board_list=self.board_list, name="card2", order=2)
		card1 = Card.objects.create(board_list=self.board_list, name="card1", order=1)
		card3 = Card.objects.create(board_list=self.board_list, name="card3", order=3)

		cards = list(Card.objects.filter(board_list=self.board_list))
		self.assertEqual(cards[0], card1)
		self.assertEqual(cards[1], card2)
		self.assertEqual(cards[2], card3)

	def test_file_upload_retain_correct_path_in_db(self):

		dummy_image = SimpleUploadedFile(
			name="test_cover.png",
			content=b'\x47\x49\x46',
			content_type="image/png"
			)

		card = Card.objects.create(board_list=self.board_list, name="card1", cover_image=dummy_image)
		now = timezone.now()
		expected_path = f"{self.user.id}/{self.board.name}/{self.board_list.name}/card1/card_cover/{now.year}/{now.month}/{now.day}/test_cover.png"

		self.assertEqual(card.cover_image.name, expected_path)

		if card.cover_image and os.path.exists(card.cover_image.path):
			os.remove(card.cover_image.path)

class BoardMembershipdModelTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username="owner", password="secure_pass_1234")
		self.invitee = User.objects.create_user(username="invited",email="invited@email.com" ,password="secure_pass_1234")
		self.board = Board.objects.create(owner=self.owner, name="Project")

	def test_string_representation(self):

		membership = BoardMembership.objects.create(user=self.invitee, board=self.board, member_type="admin")
		expected_string = f"{self.invitee} is {self.board} board admin member"
		self.assertEqual(str(membership), expected_string)

	def test_membership_default_value(self):
		membership = BoardMembership.objects.create(user=self.invitee, board=self.board)
		self.assertEqual(membership.member_type, "member")
		self.assertFalse(membership.accepted)



	def test_user_board_uniqueness_constraint(self):
		BoardMembership.objects.create(user=self.invitee, board=self.board)
		duplicate_membership = BoardMembership(user=self.invitee, board=self.board)

		with self.assertRaises(IntegrityError):
			duplicate_membership.save()

class BoardOwnerMembershipSignalTests(TestCase):

	def setUp(self):
		self.owner = User.objects.create_user(username="test_user", password="secure_pass_1234")

	def test_board_creationg_trigger_membership_signal(self):
		"""Ensure post_save signal automatically handles admin registration for the owner."""

		self.assertEqual(BoardMembership.objects.count(), 0)

		board = Board.objects.create(owner=self.owner, name="Project")

		self.assertEqual(BoardMembership.objects.count(), 1)

		membership = BoardMembership.objects.first()
		self.assertEqual(membership.board, board)
		self.assertEqual(membership.member_type, "admin")
		self.assertEqual(membership.accepted, True)

	def test_board_update_does_not_duplicate_membership(self):
		"""Ensure modifying an existing board doesn't fire duplicate membership entries."""

		board = Board.objects.create(owner=self.owner, name="Project")
		self.assertEqual(BoardMembership.objects.count(), 1)
		board.name = "New Project"
		board.save()
		self.assertEqual(BoardMembership.objects.count(), 1)


class CardMembershipdModelTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username="owner", password="secure_pass_1234")
		self.board = Board.objects.create(owner=self.owner, name="Project")
		self.board_list = BoardList.objects.create(board=self.board, name="In Progress")
		self.card = Card.objects.create(board_list=self.board_list, name="card1")
		self.invitee = User.objects.create_user(username="invited",email="invited@email.com" ,password="secure_pass_1234")


	def test_string_representation(self):

		membership = CardMembership.objects.create(user=self.invitee, card=self.card)
		expected_string = f"{self.invitee} is {self.card} card member"
		self.assertEqual(str(membership), expected_string)


	def test_user_card_uniqueness_constraint(self):
		CardMembership.objects.create(user=self.invitee, card=self.card)
		duplicate_membership = CardMembership(user=self.invitee, card=self.card)

		with self.assertRaises(IntegrityError):
			duplicate_membership.save()


class CardLabelModelTests(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username="test_user", password="secure_pass_1234")
        self.board = Board.objects.create(owner=self.user, name="Project")
        self.board_list = BoardList.objects.create(board=self.board, name="In Progress")
        self.card = Card.objects.create(board_list=self.board_list, name="card1")

    def test_card_label_string_representation(self):
        """Ensure the custom __str__ method evaluates and prints accurately without crashing."""
        label = CardLabel.objects.create(
            card=self.card, 
            name="Urgent Fix", 
            color="#ff0055"
        )
        
        expected_string = f"Urgent Fix is {self.card} label"
        self.assertEqual(str(label), expected_string)

class CheckListModelTests(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username="test_user", password="secure_pass_1234")
        self.board = Board.objects.create(owner=self.user, name="Project")
        self.board_list = BoardList.objects.create(board=self.board, name="In Progress")
        self.card = Card.objects.create(board_list=self.board_list, name="card1")

    def test_card_label_string_representation(self):
        """Ensure the custom __str__ method evaluates and prints accurately without crashing."""
        checklist = CheckList.objects.create(
            card=self.card, 
            name="Fix Bug"
        )
        
        expected_string = f"Fix Bug is {self.card} checklist"
        self.assertEqual(str(checklist), expected_string)

class ChecklistItemModelTests(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username="test_user", password="secure_pass_1234")
        self.board = Board.objects.create(owner=self.user, name="Project")
        self.board_list = BoardList.objects.create(board=self.board, name="In Progress")
        self.card = Card.objects.create(board_list=self.board_list, name="card1")
        self.checklist = CheckList.objects.create(card=self.card, name="Fix Bug")

    def test_card_label_string_representation(self):
        """Ensure the custom __str__ method evaluates and prints accurately without crashing."""
        checklist_item = ChecklistItem.objects.create(checklist=self.checklist, name="Logging", is_completed=True)
        
        expected_string = f"Logging is {self.checklist} checklist True"
        self.assertEqual(str(checklist_item), expected_string)