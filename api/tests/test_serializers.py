import io
import mimetypes
import pytest
from PIL import Image
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from django.http import Http404
from django.core.files.uploadedfile import SimpleUploadedFile
from board.models import (
    Activity, 
    Board, 
    CardLabel, 
    Card, 
    ChecklistItem, 
    CheckList, 
    Comment, 
    CardImage, 
    CardFile, 
    LinkAttachment)
from ..board.serializers import (
    ActivitySerializer, 
    ProfileSerializer, 
    UserSerializer, 
    BoardSerializer,
    CardLabelSerializer,
    CardSerializer,
    CheckListItemSerializer,
    CheckListSerializer,
    CardCommentSerializer,
    CardImage,
    CardFile,
    LinkAttachment,
    FileAttachmentSerializer,
    ImageAttachmentSerializer
    )
from account.models import Profile





class TestActivitySerializer:
    """Test suite for ActivitySerializer"""

    @pytest.fixture
    def valid_data(self, board):
        return {
            "board": board.id,
            "text": "List Created",
            "action_type": "create_list"
        }

    @pytest.fixture
    def valid_data_with_optional(self, valid_data, board_list, card):
         return {**valid_data,
            "board_list":board_list.id,
            "card":card.id,

        }

    @pytest.fixture
    def activity(self, user, board, board_list, card):
        return Activity.objects.create(
                user=user,
                board=board,
                board_list=board_list,
                card=card,
                action_type="create_list",
                text="List Created"
            )

    @pytest.fixture
    def serializer_context(self, api_request):
        return {"request": api_request}


    def test_serializer_is_valid(self, valid_data_with_optional, serializer_context):
        serializer = ActivitySerializer(data=valid_data_with_optional, context=serializer_context)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_is_valid_without_optional_fields(self, valid_data, serializer_context):
        serializer = ActivitySerializer(data=valid_data, context=serializer_context)
        assert serializer.is_valid(), serializer.errors

    def test_user_is_taken_from_request(self, valid_data, serializer_context, user):
        serializer = ActivitySerializer(data=valid_data, context=serializer_context)
        serializer.is_valid()
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["user"] == user

    def test_payload_user_is_overwritten_by_request_user(self, serializer_context, valid_data, user, another_user):
        valid_data["user"] = another_user.id
        serializer = ActivitySerializer(data=valid_data, context=serializer_context)
        serializer.is_valid()
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["user"] == user


    def test_to_internal_value_handles_missing_request(self, valid_data):
        serializer = ActivitySerializer(data=valid_data, context={})
        with pytest.raises(KeyError):
            serializer.is_valid()

    @pytest.mark.parametrize(
        "field",
        [
            "text",
            "action_type",

        ]
        )
    def test_validation_errors_for_required_fields(self, field, valid_data, serializer_context):
        valid_data.pop(field)
        serializer = ActivitySerializer(data=valid_data, context=serializer_context)
        assert not serializer.is_valid()
        assert field in serializer.errors
    # ----------------------------
    # Output
    # ----------------------------

    def test_serializer_output_contains_expected_fields(self, activity):
        serializer = ActivitySerializer(instance=activity)

        expected_fields = {
            "id",
            "user",
            "board",
            "board_list",
            "card",
            "text",
            "action_type",
            "timestamp",
        }

        assert set(serializer.data.keys()) == expected_fields
        assert serializer.data["text"] == activity.text
        assert serializer.data["board"] == activity.board.id
        assert serializer.data["user"] == activity.user.id

    def test_timestamp_is_read_only():
        serializer = ActivitySerializer()

        assert serializer.fields["timestamp"].read_only is True

    def test_timestamp_returns_created_time_in_milliseconds(self, activity):
        serializer = ActivitySerializer(instance=activity)
        expected = activity.created.timestamp() * 1000
        assert serializer.data["timestamp"] == expected

    def test_timestamp_is_read_only(self, serializer_context, valid_data):
        valid_data["timestamp"] = 123456789
        serializer = ActivitySerializer(data=valid_data, context=serializer_context)
        assert serializer.is_valid(), serializer.errors
        assert "timestamp" not in serializer.validated_data


    # ----------------------------
    # Create and Update
    # ----------------------------

    def test_create_activity_through_serializer(self, user, valid_data, serializer_context):
        serializer = ActivitySerializer(data=valid_data, context=serializer_context)
        assert serializer.is_valid(), serializer.errors
        activity = serializer.save()
        assert activity.board.id == valid_data["board"]
        assert activity.action_type == valid_data["action_type"]
        assert activity.text == valid_data["text"]
        assert activity.id is not None
        assert activity.user == user


    def test_update_activity_through_serializer(self, user, activity, serializer_context):
        update_data = {
            "text": "List Created(updated)"
        }
        serializer = ActivitySerializer(instance=activity, data=update_data, context=serializer_context, partial=True)
        assert serializer.is_valid()
        updated_activity = serializer.save()

        assert updated_activity.text == "List Created(updated)"
        assert updated_activity.user == user



@pytest.mark.django_db
class TestProfileSerializer:
    """Test suite for ProfileSerializer."""

    @pytest.fixture
    def valid_data(self, user):
        return {
            "user": user.id,
            "bio": "Software Engineer",
        }

    @pytest.fixture
    def image_file(self):
        file = io.BytesIO()
        image = Image.new("RGB", (100,100), color="red")
        image.save(file, format="JPEG")
        file.seek(0)
        return SimpleUploadedFile(
                "avatar.jpg",
                file.read(),
                content_type="image/jpeg"
            )


    @pytest.fixture
    def valid_data_with_image(self, valid_data, image_file):
        data = valid_data.copy()
        data["profile_image"] = image_file
        return data

    @pytest.fixture
    def profile(self, user):
        return Profile.objects.create(
            user=user,
            bio="Backend Developer",
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = ProfileSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    def test_serializer_with_image_is_valid(self, valid_data_with_image):
        serializer = ProfileSerializer(data=valid_data_with_image)

        assert serializer.is_valid(), serializer.errors
    def test_serializer_is_valid_without_profile_image(self, valid_data):
        serializer = ProfileSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    def test_serializer_accepts_blank_bio(self, valid_data):
        data = valid_data.copy()
        data["bio"] = ""

        serializer = ProfileSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_user_is_required(self, valid_data):
        data = valid_data.copy()
        data.pop("user")

        serializer = ProfileSerializer(data=data)

        assert not serializer.is_valid()
        assert "user" in serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, profile):
        serializer = ProfileSerializer(profile)

        expected_fields = {
            "user",
            "profile_image",
            "bio",
        }

        assert set(serializer.data.keys()) == expected_fields

    def test_serializer_outputs_correct_values(self, profile):
        serializer = ProfileSerializer(profile)

        assert serializer.data["user"] == profile.user.id
        assert serializer.data["bio"] == profile.bio
        assert serializer.data["profile_image"] is None

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_profile(self, valid_data):
        serializer = ProfileSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        profile = serializer.save()

        assert isinstance(profile, Profile)
        assert profile.user.id == valid_data["user"]
        assert profile.bio == valid_data["bio"]
        assert profile.profile_image == None

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_profile(self, profile):
        serializer = ProfileSerializer(
            instance=profile,
            data={
                "bio": "Senior Backend Developer",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated_profile = serializer.save()

        assert updated_profile.bio == "Senior Backend Developer"
        assert updated_profile.user == profile.user

    # --------------------------------------------------------
    # Read-only / Writable fields
    # --------------------------------------------------------

    def test_all_fields_are_writable(self):
        serializer = ProfileSerializer()

        assert serializer.fields["user"].read_only is False
        assert serializer.fields["profile_image"].read_only is False
        assert serializer.fields["bio"].read_only is False


@pytest.mark.django_db
class TestUserSerializer:
    """Test suite for UserSerializer."""


    @pytest.fixture
    def user_with_profile(self, user):
        profile = Profile.objects.create(user=user, bio="Backend Developer")
        return user

    @pytest.fixture
    def update_data(self):
        return {
            "username": "new_username",
            "email": "new@example.com",
            "first_name": "new_test_user",
            "last_name": "new_last_name",
            "profile": {
                "bio": "Updated bio",
            },
        }

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, user_with_profile):
        serializer = UserSerializer(user_with_profile)

        expected_fields = {
            "id",
            "username",
            "email",
            "profile_image",
            "fullname",
            "first_name",
            "last_name",
            "profile",
        }

        assert set(serializer.data.keys()) == expected_fields

    def test_serializer_returns_correct_values(self, user_with_profile):
        serializer = UserSerializer(user_with_profile)

        assert serializer.data["id"] == user_with_profile.id
        assert serializer.data["username"] == user_with_profile.username
        assert serializer.data["email"] == user_with_profile.email
        assert serializer.data["first_name"] == user_with_profile.first_name
        assert serializer.data["last_name"] == user_with_profile.last_name

    def test_serializer_returns_fullname(self, user_with_profile):
        serializer = UserSerializer(user_with_profile)

        assert (
            serializer.data["fullname"]
            == user_with_profile.get_full_name()
        )

    def test_serializer_returns_empty_profile_image_when_none(
        self,
        user_with_profile,
    ):
        serializer = UserSerializer(user_with_profile)

        assert serializer.data["profile_image"] == ""

    def test_serializer_serializes_nested_profile(self, user_with_profile):
        serializer = UserSerializer(user_with_profile)

        assert serializer.data["profile"]["user"] == user_with_profile.id
        assert serializer.data["profile"]["bio"] == "Backend Developer"

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_all_user_fields(
        self,
        user_with_profile,
        update_data,
    ):
        serializer = UserSerializer(
            instance=user_with_profile,
            data=update_data,
            partial=True
        )

        assert serializer.is_valid(), serializer.errors

        updated_user = serializer.save()

        assert updated_user.username == update_data["username"]
        assert updated_user.email == update_data["email"]
        assert updated_user.first_name == update_data["first_name"]
        assert updated_user.last_name == update_data["last_name"]


    def test_update_returns_same_instance(
        self,
        user_with_profile,
        update_data,
    ):
        serializer = UserSerializer(
            instance=user_with_profile,
            data=update_data,
            partial=True
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.pk == user_with_profile.pk

    def test_partial_update_only_user_field(
        self,
        user_with_profile,
    ):
        old_email = user_with_profile.email
        old_last_name = user_with_profile.last_name
        old_bio = user_with_profile.profile.bio

        serializer = UserSerializer(
            instance=user_with_profile,
            data={
                "first_name": "updated_name",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.first_name == "updated_name"
        assert updated.email == old_email
        assert updated.last_name == old_last_name
        assert updated.profile.bio == old_bio

    def test_partial_update_only_profile(
        self,
        user_with_profile,
    ):
        old_username = user_with_profile.username

        serializer = UserSerializer(
            instance=user_with_profile,
            data={
                "profile": {
                    "bio": "Only profile updated",
                }
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.username == old_username
        assert updated.profile.bio == "Only profile updated"

    def test_update_without_profile_data_keeps_existing_profile(
        self,
        user_with_profile,
    ):
        old_bio = user_with_profile.profile.bio

        serializer = UserSerializer(
            instance=user_with_profile,
            data={
                "username": "updated_username",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.username == "updated_username"
        assert updated.profile.bio == old_bio




@pytest.mark.django_db
class TestBoardSerializer:
    """Test suite for BoardSerializer."""

    @pytest.fixture
    def valid_data(self):
        return {
            "name": "Project Board",
            "status": "private",
            "background_color": "#ffffff",
            "closed": False,
        }

    @pytest.fixture
    def board(self, user):
        return Board.objects.create(
            owner=user,
            name="Project Board",
            status="private",
            background_color="#ffffff",
        )

    @pytest.fixture
    def serializer_context(self, api_request):
        return {"request": api_request}

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(
        self,
        valid_data,
        serializer_context,
    ):
        serializer = BoardSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

    def test_owner_is_taken_from_request(
        self,
        valid_data,
        serializer_context,
        user,
    ):
        serializer = BoardSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["owner"] == user

    def test_payload_owner_is_overwritten_by_request_user(
        self,
        valid_data,
        serializer_context,
        another_user,
        user,
    ):
        data = valid_data.copy()
        data["owner"] = another_user.id

        serializer = BoardSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["owner"] == user

    def test_missing_request_context_raises_key_error(
        self,
        valid_data,
    ):
        serializer = BoardSerializer(data=valid_data)

        with pytest.raises(KeyError):
            serializer.is_valid()

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(
        self,
        board,
        serializer_context,
    ):
        serializer = BoardSerializer(
            board,
            context=serializer_context,
        )

        assert set(serializer.data.keys()) == {
            "id",
            "owner",
            "name",
            "status",
            "background_color",
            "background_image",
            "cards",
            "is_owner",
            "closed",
        }

    def test_serializer_outputs_correct_values(
        self,
        board,
        serializer_context,
    ):
        serializer = BoardSerializer(
            board,
            context=serializer_context,
        )

        assert serializer.data["id"] == board.id
        assert serializer.data["owner"] == board.owner.id
        assert serializer.data["name"] == board.name
        assert serializer.data["status"] == board.status
        assert serializer.data["background_color"] == board.background_color
        assert serializer.data["closed"] == board.closed

    # --------------------------------------------------------
    # SerializerMethodField
    # --------------------------------------------------------

    def test_cards_returns_zero_when_board_has_no_cards(
        self,
        board,
        serializer_context,
    ):
        serializer = BoardSerializer(
            board,
            context=serializer_context,
        )

        assert serializer.data["cards"] == 0

    def test_is_owner_returns_true_for_owner(
        self,
        board,
        serializer_context,
    ):
        serializer = BoardSerializer(
            board,
            context=serializer_context,
        )

        assert serializer.data["is_owner"] is True

    def test_is_owner_returns_false_for_non_owner(
        self,
        board,
        another_user,
        request_factory,
    ):
        request = request_factory.get("/")
        request.user = another_user

        serializer = BoardSerializer(
            board,
            context={"request": request},
        )

        assert serializer.data["is_owner"] is False

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_board(
        self,
        valid_data,
        serializer_context,
        user,
    ):
        serializer = BoardSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        board = serializer.save()

        assert isinstance(board, Board)
        assert board.owner == user
        assert board.name == valid_data["name"]
        assert board.status == valid_data["status"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_board(
        self,
        board,
        serializer_context,
    ):
        serializer = BoardSerializer(
            instance=board,
            data={
                "name": "Updated Board",
            },
            partial=True,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "Updated Board"
        assert updated.owner == board.owner



@pytest.mark.django_db
class TestCardLabelSerializer:
    """Test suite for CardLabelSerializer."""

    @pytest.fixture
    def valid_data(self, card):
        return {
            "card": card.id,
            "name": "Bug",
            "color": "#ff0000",
        }

    @pytest.fixture
    def label(self, card):
        return CardLabel.objects.create(
            card=card,
            name="Bug",
            color="#ff0000",
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = CardLabelSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    @pytest.mark.parametrize(
        "field",
        [
            "card",
            "name",
            "color",
        ],
    )
    def test_required_fields(self, valid_data, field):
        data = valid_data.copy()
        data.pop(field)

        serializer = CardLabelSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, label):
        serializer = CardLabelSerializer(label)

        expected_fields = {
            "id",
            "name",
            "color",
            "card",
        }

        assert set(serializer.data.keys()) == expected_fields

    def test_serializer_outputs_correct_values(self, label):
        serializer = CardLabelSerializer(label)

        assert serializer.data["id"] == label.id
        assert serializer.data["name"] == label.name
        assert serializer.data["color"] == label.color
        assert serializer.data["card"] == label.card.id

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_label(self, valid_data):
        serializer = CardLabelSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        label = serializer.save()

        assert isinstance(label, CardLabel)
        assert label.card.id == valid_data["card"]
        assert label.name == valid_data["name"]
        assert label.color == valid_data["color"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_label(self, label):
        serializer = CardLabelSerializer(
            instance=label,
            data={
                "name": "Feature",
                "color": "#00ff00",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "Feature"
        assert updated.color == "#00ff00"
        assert updated.card == label.card



@pytest.mark.django_db
class TestCardSerializer:
    """Test suite for CardSerializer."""

    @pytest.fixture
    def valid_data(self, board_list):
        return {
            "board_list": board_list.id,
            "name": "Implement authentication",
            "completed": False,
        }

    @pytest.fixture
    def card(self, board_list):
        return Card.objects.create(
            board_list=board_list,
            name="Implement authentication",
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = CardSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    @pytest.mark.parametrize(
        "field",
        [
            "board_list",
            "name",
        ],
    )
    def test_required_fields(self, valid_data, field):
        data = valid_data.copy()
        data.pop(field)

        serializer = CardSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, card):
        serializer = CardSerializer(card)

        expected_fields = {
            "id",
            "board_list",
            "board_list_name",
            "name",
            "due_date",
            "board",
            "labels",
            "card_labels",
            "completed",
            "order",
        }

        assert set(serializer.data.keys()) == expected_fields

    def test_serializer_outputs_correct_values(self, card):
        serializer = CardSerializer(card)

        assert serializer.data["id"] == card.id
        assert serializer.data["board_list"] == card.board_list.id
        assert serializer.data["name"] == card.name
        assert serializer.data["completed"] == card.completed

    def test_get_board_returns_board_name(self, card):
        serializer = CardSerializer(card)

        assert serializer.data["board"] == card.board_list.board.name

    def test_get_board_list_name_returns_name(self, card):
        serializer = CardSerializer(card)

        assert serializer.data["board_list_name"] == card.board_list.name

    def test_get_labels_returns_empty_list(self, card):
        serializer = CardSerializer(card)

        assert list(serializer.data["labels"]) == []

    def test_get_labels_returns_label_ids(self, card):
        label1 = CardLabel.objects.create(
            card=card,
            name="Bug",
            color="#ff0000",
        )

        label2 = CardLabel.objects.create(
            card=card,
            name="Backend",
            color="#00ff00",
        )

        serializer = CardSerializer(card)

        assert set(serializer.data["labels"]) == {
            label1.id,
            label2.id,
        }

    def test_nested_card_labels_are_serialized(self, card):
        label = CardLabel.objects.create(
            card=card,
            name="Bug",
            color="#ff0000",
        )

        serializer = CardSerializer(card)

        assert len(serializer.data["card_labels"]) == 1
        assert serializer.data["card_labels"][0]["id"] == label.id
        assert serializer.data["card_labels"][0]["name"] == "Bug"
        assert serializer.data["card_labels"][0]["color"] == "#ff0000"

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_card(self, valid_data):
        serializer = CardSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        card = serializer.save()

        assert isinstance(card, Card)
        assert card.board_list.id == valid_data["board_list"]
        assert card.name == valid_data["name"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_card(self, card):
        serializer = CardSerializer(
            instance=card,
            data={
                "name": "Updated card",
                "completed": True,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "Updated card"
        assert updated.completed is True



@pytest.mark.django_db
class TestCheckListItemSerializer:
    """Test suite for CheckListItemSerializer."""

    @pytest.fixture
    def checklist(self, card):
        return CheckList.objects.create(card=card, name="Check List")

    @pytest.fixture
    def valid_data(self, checklist):
        return {
            "checklist": checklist.id,
            "name": "Write unit tests",
            "is_completed": False,
        }

    @pytest.fixture
    def checklist_item(self, checklist):
        return ChecklistItem.objects.create(
            checklist=checklist,
            name="Write unit tests",
            is_completed=False,
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = CheckListItemSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    @pytest.mark.parametrize(
        "field",
        [
            "checklist",
            "name",
        ],
    )
    def test_required_fields(self, valid_data, field):
        data = valid_data.copy()
        data.pop(field)

        serializer = CheckListItemSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, checklist_item):
        serializer = CheckListItemSerializer(checklist_item)

        expected_fields = {
            "id",
            "name",
            "is_completed",
            "checklist",
        }

        assert set(serializer.data.keys()) == expected_fields

    def test_serializer_outputs_correct_values(self, checklist_item):
        serializer = CheckListItemSerializer(checklist_item)

        assert serializer.data["id"] == checklist_item.id
        assert serializer.data["name"] == checklist_item.name
        assert serializer.data["is_completed"] == checklist_item.is_completed
        assert serializer.data["checklist"] == checklist_item.checklist.id

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_checklist_item(self, valid_data):
        serializer = CheckListItemSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        item = serializer.save()

        assert isinstance(item, ChecklistItem)
        assert item.checklist.id == valid_data["checklist"]
        assert item.name == valid_data["name"]
        assert item.is_completed is False

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_checklist_item(self, checklist_item):
        serializer = CheckListItemSerializer(
            instance=checklist_item,
            data={
                "name": "Review unit tests",
                "is_completed": True,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "Review unit tests"
        assert updated.is_completed is True
        assert updated.checklist == checklist_item.checklist


@pytest.mark.django_db
class TestCheckListSerializer:
    """Test suite for CheckListSerializer."""

    @pytest.fixture
    def valid_data(self, card):
        return {
            "card": card.id,
            "name": "Development",
        }

    @pytest.fixture
    def checklist(self, card):
        return CheckList.objects.create(
            card=card,
            name="Development",
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = CheckListSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    @pytest.mark.parametrize(
        "field",
        [
            "card",
            "name",
        ],
    )
    def test_required_fields(self, valid_data, field):
        data = valid_data.copy()
        data.pop(field)

        serializer = CheckListSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, checklist):
        serializer = CheckListSerializer(checklist)

        expected_fields = {
            "id",
            "name",
            "checklist_items",
            "card",
        }

        assert set(serializer.data.keys()) == expected_fields

    def test_serializer_outputs_correct_values(self, checklist):
        serializer = CheckListSerializer(checklist)

        assert serializer.data["id"] == checklist.id
        assert serializer.data["name"] == checklist.name
        assert serializer.data["card"] == checklist.card.id

    def test_serializer_returns_empty_checklist_items(self, checklist):
        serializer = CheckListSerializer(checklist)

        assert serializer.data["checklist_items"] == []

    def test_serializer_serializes_nested_checklist_items(self, checklist):
        item1 = ChecklistItem.objects.create(
            checklist=checklist,
            name="Write code",
            is_completed=False,
        )

        item2 = ChecklistItem.objects.create(
            checklist=checklist,
            name="Write tests",
            is_completed=True,
        )

        serializer = CheckListSerializer(checklist)

        assert len(serializer.data["checklist_items"]) == 2

        names = {
            item["name"]
            for item in serializer.data["checklist_items"]
        }

        assert names == {
            item1.name,
            item2.name,
        }

    def test_checklist_items_is_read_only(self):
        serializer = CheckListSerializer()

        assert serializer.fields["checklist_items"].read_only is True

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_checklist(self, valid_data):
        serializer = CheckListSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        checklist = serializer.save()

        assert isinstance(checklist, CheckList)
        assert checklist.card.id == valid_data["card"]
        assert checklist.name == valid_data["name"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_checklist(self, checklist):
        serializer = CheckListSerializer(
            instance=checklist,
            data={
                "name": "Updated Checklist",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "Updated Checklist"
        assert updated.card == checklist.card


@pytest.mark.django_db
class TestCardCommentSerializer:
    """Test suite for CardCommentSerializer."""



    @pytest.fixture
    def valid_data(self, card):
        return {
            "card": card.id,
            "content": "Test comment",
        }

    @pytest.fixture
    def serializer_context(self, api_request):
        return {"request": api_request}

    @pytest.fixture
    def comment(self, user, card):
        return Comment.objects.create(
            user=user,
            card=card,
            content="Test comment",
        )

    @pytest.fixture
    def card_image(self, card, user):
        test_image = SimpleUploadedFile(
                "file.jpg",
                b"fake content",
                "image/jpg"
            )
        return CardImage.objects.create(card=card, user=user, file=test_image)

    @pytest.fixture
    def card_file(self, card, user):
        test_file = SimpleUploadedFile(
                "file.csv",
                b"fake content",
                "text/csv"
            )
        return CardFile.objects.create(card=card, user=user, file=test_file)

    @pytest.fixture
    def link_attachment(self, card, user):
        link = "https://www.test.com"
        return LinkAttachment.objects.create(card=card, user=user, file=link)

    @pytest.fixture
    def comment_with_image_attachment(self, user, card, card_image):
        return Comment.objects.create(user=user, card=card, reply_content_object=card_image)

    @pytest.fixture
    def comment_with_file_attachment(self, user, card, card_file):
        return Comment.objects.create(user=user, card=card, reply_content_object=card_file)

    @pytest.fixture
    def comment_with_link_attachment(self, user, card, link_attachment):
        return Comment.objects.create(user=user, card=card, reply_content_object=link_attachment)
    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(
        self,
        valid_data,
        serializer_context,
    ):
        serializer = CardCommentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

    def test_user_is_taken_from_request(
        self,
        valid_data,
        serializer_context,
        user,
    ):
        serializer = CardCommentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["user"] == user

    def test_payload_user_is_overwritten(
        self,
        valid_data,
        serializer_context,
        user,
        another_user,
    ):
        data = valid_data.copy()
        data["user"] = another_user.id

        serializer = CardCommentSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["user"] == user

    def test_missing_request_context_raises_key_error(
        self,
        valid_data,
    ):
        serializer = CardCommentSerializer(data=valid_data)

        with pytest.raises(KeyError):
            serializer.is_valid()

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(
        self,
        comment,
    ):
        serializer = CardCommentSerializer(comment)

        assert set(serializer.data.keys()) == {
            "id",
            "user",
            "content",
            "timestamp",
            "edited",
            "card",
            "reply",
        }

    def test_serializer_outputs_correct_values(
        self,
        comment,
    ):
        serializer = CardCommentSerializer(comment)

        assert serializer.data["id"] == comment.id
        assert serializer.data["user"] == comment.user.id
        assert serializer.data["content"] == comment.content
        assert serializer.data["edited"] == comment.edited
        assert serializer.data["card"] == comment.card.id



    def test_timestamp_returns_updated_time_in_milliseconds(
        self,
        comment,
    ):
        comment.content = "edited"
        comment.save()

        serializer = CardCommentSerializer(comment)

        expected = comment.updated.timestamp() * 1000

        assert serializer.data["timestamp"] == expected

    def test_reply_returns_none_when_no_attachment(
        self,
        comment,
    ):
        serializer = CardCommentSerializer(comment)

        assert serializer.data["reply"] is None

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_comment_without_attachment(
        self,
        valid_data,
        serializer_context,
    ):
        serializer = CardCommentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        comment = serializer.save()

        assert isinstance(comment, Comment)
        assert comment.reply_content_object is None

    def test_create_comment_with_image_attachment(
        self,
        valid_data,
        serializer_context,
        card_image,
    ):
        data = valid_data.copy()
        data["reply_type"] = "image/png"
        data["reply_id"] = card_image.id

        serializer = CardCommentSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        comment = serializer.save()

        assert comment.reply_content_object == card_image

    def test_create_comment_with_file_attachment(
        self,
        valid_data,
        serializer_context,
        card_file,
    ):
        data = valid_data.copy()
        data["reply_type"] = "text/plain"
        data["reply_id"] = card_file.id

        serializer = CardCommentSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        comment = serializer.save()

        assert comment.reply_content_object == card_file

    def test_create_comment_with_link_attachment(
        self,
        valid_data,
        serializer_context,
        link_attachment,
    ):
        data = valid_data.copy()
        data["reply_type"] = "link"
        data["reply_id"] = link_attachment.id

        serializer = CardCommentSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        comment = serializer.save()

        assert comment.reply_content_object == link_attachment

    def test_invalid_attachment_id_raises_404(
        self,
        valid_data,
        serializer_context,
    ):
        data = valid_data.copy()
        data["reply_type"] = "image/png"
        data["reply_id"] = 999999

        serializer = CardCommentSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        with pytest.raises(Http404):
            serializer.save()

    # --------------------------------------------------------
    # get_reply()
    # --------------------------------------------------------

    def test_reply_for_image_attachment(
        self,
        comment_with_image_attachment,
    ):
        serializer = CardCommentSerializer(comment_with_image_attachment)

        reply = serializer.data["reply"]

        assert reply["id"] == comment_with_image_attachment.reply_content_object.id
        assert reply["type"].startswith("image/")

    def test_reply_for_file_attachment(
        self,
        comment_with_file_attachment,
    ):
        serializer = CardCommentSerializer(comment_with_file_attachment)

        reply = serializer.data["reply"]

        assert reply["id"] == comment_with_file_attachment.reply_content_object.id
        assert reply["type"] == "text/csv"

    def test_reply_for_link_attachment(
        self,
        comment_with_link_attachment,
    ):
        serializer = CardCommentSerializer(comment_with_link_attachment)

        reply = serializer.data["reply"]

        assert reply["id"] == comment_with_link_attachment.reply_content_object.id
        assert reply["type"] == "link"



@pytest.mark.django_db
class TestFileAttachmentSerializer:
    """Test suite for FileAttachmentSerializer."""

    @pytest.fixture
    def uploaded_text_file(self):
        file = SimpleUploadedFile(
                "file.txt",
                b"fake content",
                "plain/text"
            )
        return file


    @pytest.fixture
    def valid_data(self, card, uploaded_text_file):
        return {
            "card": card.id,
            "name": "Specification",
            "description": "Project specification",
            "file": uploaded_text_file,
        }

    @pytest.fixture
    def serializer_context(self, api_request):
        return {"request": api_request}


    @pytest.fixture
    def attachment(self, user, card, uploaded_text_file):
        return CardFile.objects.create(
            user=user,
            card=card,
            name="Specification",
            description="Project specification",
            file=uploaded_text_file,
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(
        self,
        valid_data,
        serializer_context,
    ):
        serializer = FileAttachmentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

    def test_user_is_taken_from_request(
        self,
        valid_data,
        serializer_context,
        user,
    ):
        serializer = FileAttachmentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["user"] == user

    def test_payload_user_is_overwritten(
        self,
        valid_data,
        serializer_context,
        user,
        another_user,
    ):
        data = valid_data.copy()
        data["user"] = another_user.id

        serializer = FileAttachmentSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["user"] == user

    def test_missing_request_context_raises_key_error(
        self,
        valid_data,
    ):
        serializer = FileAttachmentSerializer(data=valid_data)

        with pytest.raises(KeyError):
            serializer.is_valid()

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(
        self,
        attachment,
    ):
        serializer = FileAttachmentSerializer(attachment)

        assert set(serializer.data.keys()) == {
            "id",
            "name",
            "display_name",
            "description",
            "file",
            "file_type",
            "upload_at",
            "user",
            "card",
        }

    def test_serializer_outputs_correct_values(
        self,
        attachment,
    ):
        serializer = FileAttachmentSerializer(attachment)

        assert serializer.data["id"] == attachment.id
        assert serializer.data["name"] == attachment.name
        assert serializer.data["description"] == attachment.description
        assert serializer.data["user"] == attachment.user.id
        assert serializer.data["card"] == attachment.card.id

    def test_get_file_type_returns_mime_type(
        self,
        attachment,
    ):
        serializer = FileAttachmentSerializer(attachment)

        expected, _ = mimetypes.guess_type(
            attachment.file.name
        )

        assert serializer.data["file_type"] == expected

    def test_get_display_name_uses_custom_name(
        self,
        attachment,
    ):
        serializer = FileAttachmentSerializer(attachment)

        extension = attachment.file.name.rsplit(".", 1)[1]

        assert (
            serializer.data["display_name"]
            == f"Specification.{extension}"
        )

    def test_get_display_name_uses_original_filename(
        self,
        attachment,
    ):
        attachment.name = ""
        attachment.save()

        serializer = FileAttachmentSerializer(attachment)

        assert (
            serializer.data["display_name"]
            == attachment.file.name.rsplit("/", 1)[1]
        )

    def test_get_upload_at_returns_created_timestamp(
        self,
        attachment,
    ):
        serializer = FileAttachmentSerializer(attachment)

        assert (
            serializer.data["upload_at"]
            == attachment.created.timestamp()
        )

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_attachment(
        self,
        valid_data,
        serializer_context,
        user,
    ):
        serializer = FileAttachmentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        attachment = serializer.save()

        assert isinstance(attachment, CardFile)
        assert attachment.user == user
        assert attachment.card.id == valid_data["card"]
        assert attachment.name == valid_data["name"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_attachment(
        self,
        attachment,
        serializer_context
    ):
        serializer = FileAttachmentSerializer(
            instance=attachment,
            data={
                "name": "Updated",
                "description": "Updated description",
            },
            context=serializer_context,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "Updated"
        assert updated.description == "Updated description"



@pytest.mark.django_db
class TestImageAttachmentSerializer:
    """Test suite for ImageAttachmentSerializer."""

    @pytest.fixture
    def uploaded_image(self):
        file = io.BytesIO()
        image = Image.new("RGB", (100,100), color="red")
        image.save(file, format="JPEG")
        file.seek(0)
        return SimpleUploadedFile(
                "upload_image.jpg",
                file.read(),
                content_type="image/jpeg"
            )
    @pytest.fixture
    def valid_data(self, card, uploaded_image):
        return {
            "card": card.id,
            "name": "attach",
            "description": "this is attachment",
            "file": uploaded_image,
        }

    @pytest.fixture
    def serializer_context(self, api_request):
        return {"request": api_request}

    @pytest.fixture
    def image_attachment(self, user, card, uploaded_image):
        return CardImage.objects.create(
            user=user,
            card=card,
            name="attach",
            description="this is attachment",
            file=uploaded_image,
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(
        self,
        valid_data,
        serializer_context,
    ):
        print(valid_data)
        serializer = ImageAttachmentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(
        self,
        image_attachment,
    ):
        serializer = ImageAttachmentSerializer(image_attachment)

        assert set(serializer.data.keys()) == {
            "id",
            "name",
            "display_name",
            "description",
            "file",
            "file_type",
            "upload_at",
            "user",
            "card",
        }

    def test_get_file_type_returns_image_mime_type(
        self,
        image_attachment,
    ):
        serializer = ImageAttachmentSerializer(image_attachment)

        expected, _ = mimetypes.guess_type(
            image_attachment.file.name
        )

        assert serializer.data["file_type"] == expected

    def test_get_display_name_returns_custom_name(
        self,
        image_attachment,
    ):
        serializer = ImageAttachmentSerializer(image_attachment)

        extension = image_attachment.file.name.rsplit(".", 1)[1]

        assert (
            serializer.data["display_name"]
            == f"attach.{extension}"
        )

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_image_attachment(
        self,
        valid_data,
        serializer_context,
        user,
    ):
        serializer = ImageAttachmentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        image = serializer.save()

        assert isinstance(image, CardImage)
        assert image.user == user
        assert image.card.id == valid_data["card"]