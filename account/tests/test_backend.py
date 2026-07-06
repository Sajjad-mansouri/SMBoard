import pytest

from django.contrib.auth import authenticate

from api.tests.conftest import UserFactory


@pytest.mark.django_db
class TestEmailBackend:
    """Tests for EmailBackend authentication."""

    @pytest.fixture
    def password(self):
        return "secure_pass_1234"

    @pytest.fixture
    def user(self):
        return UserFactory(
            username="john",
            email="john@example.com",
        )

    # ------------------------------------------------------------------
    # Email authentication
    # ------------------------------------------------------------------

    def test_can_authenticate_with_email(
        self,
        user,
        password,
    ):
        authenticated_user = authenticate(
            username=user.email,
            password=password,
        )

        assert authenticated_user == user

    # ------------------------------------------------------------------
    # Username authentication
    # ------------------------------------------------------------------

    def test_default_backend_still_authenticates_username(
        self,
        user,
        password,
    ):
        authenticated_user = authenticate(
            username=user.username,
            password=password,
        )

        assert authenticated_user == user

    # ------------------------------------------------------------------
    # Wrong password
    # ------------------------------------------------------------------

    def test_wrong_password_returns_none(
        self,
        user,
    ):
        authenticated_user = authenticate(
            username=user.email,
            password="wrong-password",
        )

        assert authenticated_user is None

    # ------------------------------------------------------------------
    # Unknown email
    # ------------------------------------------------------------------

    def test_unknown_email_returns_none(
        self,
        password,
    ):
        authenticated_user = authenticate(
            username="unknown@example.com",
            password=password,
        )

        assert authenticated_user is None

    # ------------------------------------------------------------------
    # Inactive user
    # ------------------------------------------------------------------

    def test_inactive_user_cannot_authenticate(
        self,
        user,
        password,
    ):
        user.is_active = False
        user.save(update_fields=["is_active"])

        authenticated_user = authenticate(
            username=user.email,
            password=password,
        )

        assert authenticated_user is None

    # ------------------------------------------------------------------
    # Missing username
    # ------------------------------------------------------------------

    def test_missing_username_returns_none(
        self,
        password,
    ):
        authenticated_user = authenticate(
            username=None,
            password=password,
        )

        assert authenticated_user is None

    # ------------------------------------------------------------------
    # Missing password
    # ------------------------------------------------------------------

    def test_missing_password_returns_none(
        self,
        user,
    ):
        authenticated_user = authenticate(
            username=user.email,
            password=None,
        )

        assert authenticated_user is None