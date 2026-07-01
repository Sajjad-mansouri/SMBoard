import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from board.models import Activity, Board
from ..board.serializers import ActivitySerializer, ProfileSerializer, UserSerializer, BoardSerializer
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
        return SimpleUploadedFile(
            "avatar.jpg",
            b"fake image content",
            content_type="image/jpg"
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