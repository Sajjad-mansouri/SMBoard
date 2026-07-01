import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from board.models import Activity
from ..board.serializers import ActivitySerializer, ProfileSerializer
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