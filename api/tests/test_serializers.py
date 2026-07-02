import io
import mimetypes
import pytest
from PIL import Image
from datetime import timedelta
from django.utils import timezone
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
    LinkAttachment,
    CardMembership,
    CardWatch,
    Comment,
    BoardMembership,
    BoardList
    )
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
    ImageAttachmentSerializer,
    LinkAttachmentSerializer,
    CardMembershipSerializer,
    CardNestedSerializer,
    CardArchivedSerializer,
    BoardMembershipSerializer,
    BoardListOrderSerializer,
    BoardListSerializer,
    BoardListArchivedSerializer
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



@pytest.mark.django_db
class TestLinkAttachmentSerializer:
    """Test suite for LinkAttachmentSerializer."""

    @pytest.fixture
    def valid_data(self, card):
        return {
            "card": card.id,
            "name": "SMBoard",
            "description": "Official website",
            "file": "https://test-website.com",
        }

    @pytest.fixture
    def serializer_context(self, api_request):
        return {"request": api_request}

    @pytest.fixture
    def link_attachment(self, user, card):
        return LinkAttachment.objects.create(
            user=user,
            card=card,
            name="SMBoard",
            description="Official website",
            file="https://test-website.com",
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(
        self,
        valid_data,
        serializer_context,
    ):
        serializer = LinkAttachmentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(
        self,
        link_attachment,
    ):
        serializer = LinkAttachmentSerializer(link_attachment)

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

    def test_get_file_type_returns_link(
        self,
        link_attachment,
    ):
        serializer = LinkAttachmentSerializer(link_attachment)

        assert serializer.data["file_type"] == "link"

    def test_get_display_name_returns_url(
        self,
        link_attachment,
    ):
        serializer = LinkAttachmentSerializer(link_attachment)

        assert (
            serializer.data["display_name"]
            == link_attachment.file
        )

    def test_get_upload_at_returns_created_timestamp(
        self,
        link_attachment,
    ):
        serializer = LinkAttachmentSerializer(link_attachment)

        assert (
            serializer.data["upload_at"]
            == link_attachment.created.timestamp()
        )

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_link_attachment(
        self,
        valid_data,
        serializer_context,
        user,
    ):
        serializer = LinkAttachmentSerializer(
            data=valid_data,
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        attachment = serializer.save()

        assert isinstance(attachment, LinkAttachment)
        assert attachment.user == user
        assert attachment.card.id == valid_data["card"]
        assert attachment.file == valid_data["file"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_link_attachment(
        self,
        link_attachment,
        serializer_context
    ):
        serializer = LinkAttachmentSerializer(
            instance=link_attachment,
            data={
                "name": "SMBoard",
                "file": "https://test-website.com",
            },
            context=serializer_context,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "SMBoard"
        assert updated.file == "https://test-website.com"



@pytest.mark.django_db
class TestCardMembershipSerializer:
    """Test suite for CardMembershipSerializer."""

    @pytest.fixture
    def valid_data(self, user, card):
        return {
            "user": user.id,
            "card": card.id,
        }

    @pytest.fixture
    def membership(self, user, card):
        return CardMembership.objects.create(
            user=user,
            card=card,
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = CardMembershipSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    @pytest.mark.parametrize(
        "field",
        [
            "user",
            "card",
        ],
    )
    def test_required_fields(self, valid_data, field):
        data = valid_data.copy()
        data.pop(field)

        serializer = CardMembershipSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, membership):
        serializer = CardMembershipSerializer(membership)

        assert set(serializer.data.keys()) == {
            "id",
            "user",
            "card",
        }

    def test_serializer_outputs_correct_values(self, membership):
        serializer = CardMembershipSerializer(membership)

        assert serializer.data["id"] == membership.id
        assert serializer.data["user"] == membership.user.id
        assert serializer.data["card"] == membership.card.id

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_membership(self, valid_data):
        serializer = CardMembershipSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        membership = serializer.save()

        assert isinstance(membership, CardMembership)
        assert membership.user.id == valid_data["user"]
        assert membership.card.id == valid_data["card"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_membership(self, membership, another_user):
        serializer = CardMembershipSerializer(
            instance=membership,
            data={
                "user": another_user.id,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.user == another_user
        assert updated.card == membership.card



@pytest.mark.django_db
class TestCardNestedSerializer:
    """Test suite for CardNestedSerializer."""

    @pytest.fixture
    def valid_data(self, board_list):
        return {
            "board_list": board_list.id,
            "name": "Implement authentication",
            "description": "Card description",
            "completed": False,
            "start_date": "2026-07-01",
            "due_date": "2026-07-10T14:30",
        }
    @pytest.fixture
    def valid_data_create(self, board_list):
        return {
            "board_list": board_list,
            "name": "Implement authentication",
            "description": "Card description",
            "completed": False,
            "start_date": timezone.now().date(),
            "due_date": timezone.now() + timedelta(days=2),
        }

    @pytest.fixture
    def serializer_context(self, api_request):
        return {"request": api_request}

    @pytest.fixture
    def card_with_activity(self, user, board, board_list, card):
        activity = Activity.objects.create(user=user, board=board, board_list=board_list, card=card, action_type="edit_card_title", text="Card Title Changed")
        return card

    @pytest.fixture
    def card_with_cover_image(self, board_list, valid_data_create, simple_uploaded_image_file):

        valid_data_create["cover_image"] = simple_uploaded_image_file
        card = Card.objects.create(**valid_data_create)
        return card

    @pytest.fixture
    def card_with_cover_image_fk(self, user, card, board_list, valid_data_create, simple_uploaded_image_file):

        card_image = CardImage.objects.create(user=user, card=card, file=simple_uploaded_image_file)
        valid_data_create["cover_image_fk"] = card_image
        return Card.objects.create(**valid_data_create)

    @pytest.fixture
    def watched_card(self, user, card):
        card_watch = CardWatch.objects.create(user=user, card=card, watch=True)
        return card

    @pytest.fixture
    def card_with_comment(self, user, card):
        Comment.objects.create(user=user, card=card, content="comment")
        return card

    @pytest.fixture
    def card_with_file_attachment(self, user, card, simple_uploaded_file):
        CardFile.objects.create(user=user, card=card, file=simple_uploaded_file)
        return card

    @pytest.fixture
    def card_with_image_attachment(self, user, card, simple_uploaded_image_file):
        CardImage.objects.create(user=user, card=card, file=simple_uploaded_image_file)
        return card

    @pytest.fixture
    def card_with_link_attachment(self, user, card, simple_uploaded_image_file):
        address = "https://test-website.com"
        LinkAttachment.objects.create(user=user, card=card, file=address)
        return card

    @pytest.fixture
    def card_with_membership(self, user, card):
        CardMembership.objects.create(user=user, card=card)
        return card

    @pytest.fixture
    def card_with_checklist(self, user, card):
        CheckList.objects.create(card=card, name="Checklist One")
        return card

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = CardNestedSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    def test_start_date_accepts_none(self, valid_data):
        data = valid_data.copy()
        data["start_date"] = None

        serializer = CardNestedSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_due_date_accepts_none(self, valid_data):
        data = valid_data.copy()
        data["due_date"] = None

        serializer = CardNestedSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_invalid_start_date(self, valid_data):
        data = valid_data.copy()
        data["start_date"] = "01-07-2026"

        serializer = CardNestedSerializer(data=data)

        assert not serializer.is_valid()
        assert "start_date" in serializer.errors

    def test_invalid_due_date(self, valid_data):
        data = valid_data.copy()
        data["due_date"] = "2026/07/10"

        serializer = CardNestedSerializer(data=data)

        assert not serializer.is_valid()
        assert "due_date" in serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_contains_expected_fields(
        self,
        card,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card,
            context=serializer_context,
        )

        expected = {
            "id",
            "board_list",
            "board_list_name",
            "name",
            "description",
            "start_date",
            "due_date",
            "board",
            "labels",
            "card_labels",
            "completed",
            "order",
            "archived",
            "cover_image",
            "cover_image_fk",
            "cover_img",
            "cover_color",
            "card_memberships",
            "card_checklists",
            "card_comments",
            "watched",
            "cardfile_set",
            "cardimage_set",
            "linkattachment_set",
            "card_activities",
        }

        assert set(serializer.data.keys()) == expected

    # --------------------------------------------------------
    # cover_img
    # --------------------------------------------------------

    def test_cover_img_returns_empty_string(
        self,
        card,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card,
            context=serializer_context,
        )

        assert serializer.data["cover_img"] == ""

    def test_cover_img_uses_cover_image(
        self,
        card_with_cover_image,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_cover_image,
            context=serializer_context,
        )

        assert (
            serializer.data["cover_img"]
            == card_with_cover_image.cover_image.url
        )

    def test_cover_img_uses_cover_image_fk(
        self,
        card_with_cover_image_fk,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_cover_image_fk,
            context=serializer_context,
        )

        assert (
            serializer.data["cover_img"]
            == card_with_cover_image_fk.cover_image_fk.file.url
        )

    # --------------------------------------------------------
    # watched
    # --------------------------------------------------------

    def test_watched_returns_false(
        self,
        card,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card,
            context=serializer_context,
        )

        assert serializer.data["watched"] is False

    def test_watched_returns_true(
        self,
        watched_card,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            watched_card,
            context=serializer_context,
        )

        assert serializer.data["watched"] is True

    # --------------------------------------------------------
    # Nested serializers
    # --------------------------------------------------------

    def test_memberships_are_serialized(
        self,
        card_with_membership,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_membership,
            context=serializer_context,
        )

        assert len(serializer.data["card_memberships"]) == 1

    def test_checklists_are_serialized(
        self,
        card_with_checklist,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_checklist,
            context=serializer_context,
        )

        assert len(serializer.data["card_checklists"]) == 1

    def test_comments_are_serialized(
        self,
        card_with_comment,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_comment,
            context=serializer_context,
        )

        assert len(serializer.data["card_comments"]) == 1

    def test_file_attachments_are_serialized(
        self,
        card_with_file_attachment,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_file_attachment,
            context=serializer_context,
        )

        assert len(serializer.data["cardfile_set"]) == 1

    def test_image_attachments_are_serialized(
        self,
        card_with_image_attachment,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_image_attachment,
            context=serializer_context,
        )

        assert len(serializer.data["cardimage_set"]) == 1

    def test_link_attachments_are_serialized(
        self,
        card_with_link_attachment,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_link_attachment,
            context=serializer_context,
        )

        assert len(serializer.data["linkattachment_set"]) == 1

    def test_activities_are_serialized(
        self,
        card_with_activity,
        serializer_context,
    ):
        serializer = CardNestedSerializer(
            card_with_activity,
            context=serializer_context,
        )

        assert len(serializer.data["card_activities"]) == 1

    # --------------------------------------------------------
    # Field configuration
    # --------------------------------------------------------

    def test_archived_is_read_only(self):
        serializer = CardNestedSerializer()

        assert serializer.fields["archived"].read_only is True



@pytest.mark.django_db
class TestCardArchivedSerializer:
    """Test suite for CardArchivedSerializer."""

    @pytest.fixture
    def valid_data(self):
        return {
            "name": "Updated Card",
            "archived": True,
        }

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = CardArchivedSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors


    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, card):
        serializer = CardArchivedSerializer(card)

        assert set(serializer.data.keys()) == {
            "name",
            "archived",
        }

    def test_serializer_outputs_correct_values(self, card):
        serializer = CardArchivedSerializer(card)

        assert serializer.data["name"] == card.name
        assert serializer.data["archived"] == card.archived

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_archived_status(self, card):
        serializer = CardArchivedSerializer(
            instance=card,
            data={
                "archived": True,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.archived is True
        assert updated.name == card.name

    def test_update_name(self, card):
        serializer = CardArchivedSerializer(
            instance=card,
            data={
                "name": "Archived Card",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "Archived Card"
        assert updated.archived == card.archived

    def test_update_name_and_archived(self, card):
        serializer = CardArchivedSerializer(
            instance=card,
            data={
                "name": "Archived Card",
                "archived": True,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "Archived Card"
        assert updated.archived is True



@pytest.mark.django_db
class TestBoardMembershipSerializer:
    """Test suite for BoardMembershipSerializer."""

    @pytest.fixture
    def valid_data(self, another_user, board):
        return {
            "user_id": another_user.id,
            "board": board.id,
            "member_type": "member",
            "accepted": False,
        }

    @pytest.fixture
    def membership(self, another_user, board):
        return BoardMembership.objects.create(
            user=another_user,
            board=board,
            member_type="member",
            accepted=False,
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = BoardMembershipSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    @pytest.mark.parametrize(
        "field",
        [
            "user_id",
            "board",
        ],
    )
    def test_required_fields(self, valid_data, field):
        data = valid_data.copy()
        data.pop(field)

        serializer = BoardMembershipSerializer(data=data)
        assert not serializer.is_valid()
        assert field in serializer.errors

    def test_user_id_maps_to_user(self, valid_data, another_user):
        serializer = BoardMembershipSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["user"] == another_user

    def test_user_field_is_read_only(self, valid_data, another_user):
        data = valid_data.copy()
        data["user"] = another_user.id

        serializer = BoardMembershipSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["user"].id == valid_data["user_id"]

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, membership):
        serializer = BoardMembershipSerializer(membership)

        assert set(serializer.data.keys()) == {
            "id",
            "user",
            "member_type",
            "accepted",
            "board",
        }

    def test_user_id_is_write_only(self, membership):
        serializer = BoardMembershipSerializer(membership)

        assert "user_id" not in serializer.data

    def test_user_is_nested_serializer(self, membership):
        serializer = BoardMembershipSerializer(membership)

        assert serializer.data["user"]["id"] == membership.user.id
        assert serializer.data["user"]["username"] == membership.user.username

    def test_serializer_outputs_correct_values(self, membership):
        serializer = BoardMembershipSerializer(membership)

        assert serializer.data["id"] == membership.id
        assert serializer.data["board"] == membership.board.id
        assert serializer.data["member_type"] == membership.member_type
        assert serializer.data["accepted"] == membership.accepted

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_membership(self, valid_data, another_user):
        serializer = BoardMembershipSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        membership = serializer.save()

        assert isinstance(membership, BoardMembership)
        assert membership.user == another_user
        assert membership.board.id == valid_data["board"]
        assert membership.member_type == valid_data["member_type"]
        assert membership.accepted == valid_data["accepted"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_membership(self, membership):
        serializer = BoardMembershipSerializer(
            instance=membership,
            data={
                "accepted": True,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.accepted is True
        assert updated.user == membership.user
        assert updated.board == membership.board

    # --------------------------------------------------------
    # Field configuration
    # --------------------------------------------------------

    def test_user_field_is_read_only(self):
        serializer = BoardMembershipSerializer()

        assert serializer.fields["user"].read_only is True

    def test_user_id_field_is_write_only(self):
        serializer = BoardMembershipSerializer()

        assert serializer.fields["user_id"].write_only is True



@pytest.mark.django_db
class TestBoardListOrderSerializer:
    """Test suite for BoardListOrderSerializer."""

    @pytest.fixture
    def board_lists(self, board):
        return [
            BoardList.objects.create(
                board=board,
                name="Todo",
                order=0,
            ),
            BoardList.objects.create(
                board=board,
                name="Doing",
                order=1,
            ),
            BoardList.objects.create(
                board=board,
                name="Done",
                order=2,
            ),
        ]

    @pytest.fixture
    def valid_data(self, board_lists):
        return [
            {
                "id": board_lists[0].id,
                "order": 2,
            },
            {
                "id": board_lists[1].id,
                "order": 0,
            },
            {
                "id": board_lists[2].id,
                "order": 1,
            },
        ]

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, board_lists, valid_data):
        serializer = BoardListOrderSerializer(
            instance=board_lists,
            data=valid_data,
            many=True,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

    def test_id_is_required(self, board_lists):
        serializer = BoardListOrderSerializer(
            instance=board_lists,
            data=[
                {
                    "order": 5,
                }
            ],
            many=True,
            partial=True,
        )

        assert not serializer.is_valid()

        assert "non_field_errors" in serializer.errors
        assert serializer.errors["non_field_errors"] == [
            "Each object must include an id."
        ]

    # --------------------------------------------------------
    # Bulk Update
    # --------------------------------------------------------

    def test_bulk_update(self, board_lists, valid_data):
        serializer = BoardListOrderSerializer(
            instance=board_lists,
            data=valid_data,
            many=True,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        for obj in board_lists:
            obj.refresh_from_db()

        assert len(updated) == 3
        assert board_lists[0].order == 2
        assert board_lists[1].order == 0
        assert board_lists[2].order == 1

    def test_returns_updated_instances(self, board_lists, valid_data):
        serializer = BoardListOrderSerializer(
            instance=board_lists,
            data=valid_data,
            many=True,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert len(updated) == 3
        assert all(isinstance(obj, BoardList) for obj in updated)

    def test_partial_update_preserves_other_fields(self, board_lists):
        old_name = board_lists[0].name

        serializer = BoardListOrderSerializer(
            instance=board_lists,
            data=[
                {
                    "id": board_lists[0].id,
                    "order": 100,
                }
            ],
            many=True,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        serializer.save()

        board_lists[0].refresh_from_db()

        assert board_lists[0].order == 100
        assert board_lists[0].name == old_name

    def test_unknown_id_is_ignored(self, board_lists):
        serializer = BoardListOrderSerializer(
            instance=board_lists,
            data=[
                {
                    "id": 999999,
                    "order": 5,
                }
            ],
            many=True,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated == []

        for index, board_list in enumerate(board_lists):
            board_list.refresh_from_db()
            assert board_list.order == index

    def test_empty_list_returns_empty_list(self, board_lists):
        serializer = BoardListOrderSerializer(
            instance=board_lists,
            data=[],
            many=True,
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated == []

    # --------------------------------------------------------
    # Duplicate IDs
    # --------------------------------------------------------

    def test_duplicate_ids_raise_validation_error(self, board_lists):
        serializer = BoardListOrderSerializer(
            instance=board_lists,
            data=[
                {
                    "id": board_lists[0].id,
                    "order": 10,
                },
                {
                    "id": board_lists[0].id,
                    "order": 99,
                },
            ],
            many=True,
            partial=True,
        )

        assert not serializer.is_valid()

        assert "Duplicate ids are not allowed." in str(serializer.errors)

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, board_lists):
        serializer = BoardListOrderSerializer(
            board_lists,
            many=True,
        )

        expected_fields = {
            "id", 
            "order", 
            "name", 
            "cover_image", 
            "cover_color", 
            "list_cards", 
            "archived",
            "board"
        }

        assert set(serializer.data[0].keys()) == expected_fields



@pytest.mark.django_db
class TestBoardListSerializer:
    """Test suite for BoardListSerializer."""

    @pytest.fixture
    def valid_data(self, board):
        return {
            "board": board.id,
            "name": "To Do",
            "order": 0,
            "cover_color": "#ffffff",
            "archived": False,
        }

    @pytest.fixture
    def board_list(self, board):
        return BoardList.objects.create(
            board=board,
            name="To Do",
            order=0,
            cover_color="#ffffff",
            archived=False,
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = BoardListSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    @pytest.mark.parametrize(
        "field",
        [
            "board",
            "name",
        ],
    )
    def test_required_fields(self, valid_data, field):
        data = valid_data.copy()
        data.pop(field)

        serializer = BoardListSerializer(data=data)

        assert not serializer.is_valid()
        assert field in serializer.errors

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_fields(self, board_list):
        serializer = BoardListSerializer(board_list)

        expected_fields = {
            "id",
            "order",
            "name",
            "cover_image",
            "cover_color",
            "list_cards",
            "archived",
            "board",
        }

        assert set(serializer.data.keys()) == expected_fields

    def test_serializer_outputs_correct_values(self, board_list):
        serializer = BoardListSerializer(board_list)

        assert serializer.data["id"] == board_list.id
        assert serializer.data["name"] == board_list.name
        assert serializer.data["order"] == board_list.order
        assert serializer.data["board"] == board_list.board.id
        assert serializer.data["archived"] == board_list.archived
        assert serializer.data["cover_color"] == board_list.cover_color

    def test_list_cards_is_empty(self, board_list):
        serializer = BoardListSerializer(board_list)

        assert serializer.data["list_cards"] == []

    def test_nested_cards_are_serialized(self, board_list, card, serializer_context):
        serializer = BoardListSerializer(board_list, context=serializer_context)

        assert len(serializer.data["list_cards"]) == 1
        assert serializer.data["list_cards"][0]["id"] == card.id
        assert serializer.data["list_cards"][0]["name"] == card.name

    def test_nested_cards_without_context(self, board_list, card, serializer_context):
        serializer = BoardListSerializer(board_list)
        assert len(serializer.data["list_cards"]) == 1
        assert serializer.data["list_cards"][0]["watched"] == None

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    def test_create_board_list(self, valid_data):
        serializer = BoardListSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

        board_list = serializer.save()

        assert isinstance(board_list, BoardList)
        assert board_list.name == valid_data["name"]
        assert board_list.board.id == valid_data["board"]
        assert board_list.cover_color == valid_data["cover_color"]
        assert board_list.archived == valid_data["archived"]

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_board_list(self, board_list):
        serializer = BoardListSerializer(
            instance=board_list,
            data={
                "name": "In Progress",
                "cover_color": "#000000",
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.name == "In Progress"
        assert updated.cover_color == "#000000"
        assert updated.board == board_list.board



@pytest.mark.django_db
class TestBoardListArchivedSerializer:
    """Test suite for BoardListArchivedSerializer."""

    @pytest.fixture
    def valid_data(self):
        return {
            "archived": True,
        }

    @pytest.fixture
    def board_list(self, board):
        return BoardList.objects.create(
            board=board,
            name="To Do",
            archived=False,
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def test_serializer_is_valid(self, valid_data):
        serializer = BoardListArchivedSerializer(data=valid_data)

        assert serializer.is_valid(), serializer.errors

    def test_archived_is_default_false(self):
        serializer = BoardListArchivedSerializer(data={})

        assert serializer.is_valid()


    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def test_serializer_output_contains_expected_field(self, board_list):
        serializer = BoardListArchivedSerializer(board_list)

        assert set(serializer.data.keys()) == {"archived"}

    def test_serializer_outputs_correct_value(self, board_list):
        serializer = BoardListArchivedSerializer(board_list)

        assert serializer.data["archived"] == board_list.archived

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    def test_update_archived(self, board_list):
        serializer = BoardListArchivedSerializer(
            instance=board_list,
            data={
                "archived": True,
            },
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.archived is True

    def test_partial_update(self, board_list):
        serializer = BoardListArchivedSerializer(
            instance=board_list,
            data={},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

        updated = serializer.save()

        assert updated.archived is False