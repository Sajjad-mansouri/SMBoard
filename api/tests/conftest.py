import io
import factory
import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from factory.django import DjangoModelFactory
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model
from board.models import Board, BoardList, Card, Activity

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