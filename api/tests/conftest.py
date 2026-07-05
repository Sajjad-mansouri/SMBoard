import io
import factory
import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from factory.django import DjangoModelFactory
from rest_framework.test import APIRequestFactory, APIClient
from django.contrib.auth import get_user_model
from board.models import (
	Board, 
	BoardList, 
	Card, 
	Activity, 
	CheckList, 
	ChecklistItem, 
	Comment,
	CardFile,
	CardImage,
	LinkAttachment,
	CardLabel,
	CardMembership,
	BoardMembership,
	BoardWatch,
	CardWatch,
	Activity
	)
from account.models import Notification, Profile
User = get_user_model()


class UserFactory(DjangoModelFactory):
	"""Factory for creating User instance"""

	class Meta:
		model = User
		skip_postgeneration_save = True

	username = factory.Sequence(lambda n: f"user_{n}")
	email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
	password = factory.PostGenerationMethodCall("set_password", "secure_pass_1234")
	first_name = factory.Faker("first_name")
	last_name = factory.Faker("last_name")

class ProfileFactory(DjangoModelFactory):
	"""Factory for creating Profile instance"""

	class Meta:
		model = Profile
		

	user = factory.SubFactory(UserFactory)

class BoardFactory(DjangoModelFactory):
	"""Factory for creating Board instance"""

	class Meta:
		model = Board

	name = factory.Sequence(lambda n: f"Test Board {n}")
	owner = factory.SubFactory(UserFactory)

class BoardListFactory(DjangoModelFactory):
	"""Factory for creating BoardList instance"""

	class Meta:
		model = BoardList

	name = factory.Sequence(lambda n: f"Test List {n}")
	board = factory.SubFactory(BoardFactory)

class CardFactory(DjangoModelFactory):
	"""Factory for creating Card instance"""

	class Meta:
		model = Card

	name = factory.Sequence(lambda n: f"Test Card {n}")
	board_list = factory.SubFactory(BoardListFactory)

class CheckListFactory(DjangoModelFactory):
	"""Factory for creating CheckList instance"""

	class Meta:
		model = CheckList

	card = factory.SubFactory(CardFactory)
	name = factory.Sequence(lambda n: f"Checklist {n}")

class CheckListItemFactory(DjangoModelFactory):
	"""Factory for creating CheckListItem instance"""

	class Meta:
		model = ChecklistItem

	checklist = factory.SubFactory(CheckListFactory)
	name = factory.Sequence(lambda n: f"item {n}")

class CommentFactory(DjangoModelFactory):
	"""Factory for creating Comment instance"""

	class Meta:
		model = Comment

	user = factory.SubFactory(UserFactory)
	card = factory.SubFactory(CardFactory)
	content = factory.Sequence(lambda n: f"comment {n}")


class CardFileFactory(DjangoModelFactory):
	"""Factory for creating CardFile instance"""

	class Meta:
		model = CardFile

	user = factory.SubFactory(UserFactory)
	card = factory.SubFactory(CardFactory)
	file = factory.django.FileField(filename="file.txt")

class CardImageFactory(DjangoModelFactory):
	"""Factory for creating CardImage instance"""

	class Meta:
		model = CardImage

	user = factory.SubFactory(UserFactory)
	card = factory.SubFactory(CardFactory)
	file = factory.django.ImageField(filename="image.jpg")

class LinkAttachmentFactory(DjangoModelFactory):
	"""Factory for creating LinkAttachment instance"""

	class Meta:
		model = LinkAttachment

	user = factory.SubFactory(UserFactory)
	card = factory.SubFactory(CardFactory)
	file = factory.Faker("url")

class CardLabelFactory(DjangoModelFactory):
	"""Factory for creating CardLabel instance"""

	class Meta:
		model = CardLabel

	card = factory.SubFactory(CardFactory)
	name = "To do"
	color = "#4287f5"


class CardMembershipFactory(DjangoModelFactory):
	"""Factory for creating CardMembership instance"""

	class Meta:
		model = CardMembership

	card = factory.SubFactory(CardFactory)
	user = factory.SubFactory(UserFactory)

class BoardMembershipFactory(DjangoModelFactory):
	"""Factory for creating BoardMembership instance"""

	class Meta:
		model = BoardMembership

	board = factory.SubFactory(BoardFactory)
	user = factory.SubFactory(UserFactory)
	member_type = "member"
	accepted = True

class NotificationFactory(DjangoModelFactory):
	"""Factory for creating Notification instance"""

	class Meta:
		model = Notification


	user = factory.SubFactory(UserFactory)

class BoardWatchFactory(DjangoModelFactory):
	"""Factory for creating BoardWatch instance"""

	class Meta:
		model = BoardWatch


	user = factory.SubFactory(UserFactory)
	board = factory.SubFactory(BoardFactory)
	watch = False

class CardWatchFactory(DjangoModelFactory):
	"""Factory for creating CardWatch instance"""

	class Meta:
		model = CardWatch


	user = factory.SubFactory(UserFactory)
	card = factory.SubFactory(CardFactory)
	watch = False

class ActivityFactory(DjangoModelFactory):
	"""Factory for creating Activity instance"""

	class Meta:
		model = Activity


	user = factory.SubFactory(UserFactory)
	board = factory.SubFactory(BoardListFactory)
	board_list = factory.SubFactory(BoardListFactory)
	card = factory.SubFactory(CardFactory)
	action_type = "create_card"
	text = "Card Created"

@pytest.fixture
def user(db):
	"""create and return basic User"""
	return UserFactory()


@pytest.fixture
def another_user(db):
	"""create and return another User"""
	return UserFactory()

@pytest.fixture
def board(db, user):
	"""create and return a Board"""
	return BoardFactory(owner=user)

@pytest.fixture
def board_list(db, board):
	"""create and return a BoardList"""
	return BoardListFactory(board=board)

@pytest.fixture
def card(db, board_list):
	"""create and return a Card"""
	return CardFactory(board_list=board_list)

@pytest.fixture
def request_factory():
	return APIRequestFactory()

@pytest.fixture
def api_request(user, request_factory):
	request = request_factory.post("/")
	request.user = user
	return request


@pytest.fixture
def simple_uploaded_image_file():
        file = io.BytesIO()
        image = Image.new("RGB", (100,100), color="red")
        image.save(file, format="JPEG")
        file.seek(0)
        return SimpleUploadedFile(
                "img_file.jpg",
                file.read(),
                content_type="image/jpeg"
            )

@pytest.fixture
def simple_uploaded_file():
        return SimpleUploadedFile(
                "file.txt",
                b"fake content",
                content_type="plain/text"
            )

@pytest.fixture
def serializer_context(api_request):
    return {"request": api_request}


@pytest.fixture
def api_client():
	return APIClient()