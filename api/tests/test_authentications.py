import pytest

from django.urls import reverse

from .conftest import UserFactory
from django.contrib.auth import get_user_model


@pytest.mark.django_db
class TestTokenObtainPairView:
    """Tests for JWT token obtain endpoint."""

    @pytest.fixture
    def url(self):
        return reverse("token_obtain_pair")

    @pytest.fixture
    def password(self):
        return "secure_pass_1234"

    @pytest.fixture
    def user(self):
        return UserFactory(
            username="john",
        )

    # ------------------------------------------------------------------
    # Success
    # ------------------------------------------------------------------

    def test_user_can_obtain_jwt_tokens(
        self,
        api_client,
        url,
        user,
        password,
    ):

        response = api_client.post(
            url,
            {
                "username": user.username,
                "password": password,
            },
            format="json",
        )


        assert response.status_code == 200

        assert "access" in response.data
        assert "refresh" in response.data

        assert isinstance(response.data["access"], str)
        assert isinstance(response.data["refresh"], str)

    # ------------------------------------------------------------------
    # Invalid password
    # ------------------------------------------------------------------

    def test_invalid_password_returns_401(
        self,
        api_client,
        url,
        user,
    ):
        response = api_client.post(
            url,
            {
                "username": user.username,
                "password": "WrongPassword123!",
            },
            format="json",
        )

        assert response.status_code == 401

        assert "access" not in response.data
        assert "refresh" not in response.data

    # ------------------------------------------------------------------
    # Unknown user
    # ------------------------------------------------------------------

    def test_unknown_username_returns_401(
        self,
        api_client,
        url,
    ):
        response = api_client.post(
            url,
            {
                "username": "does_not_exist",
                "password": "Password123!",
            },
            format="json",
        )

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "payload,missing_field",
        [
            ({"password": "Password123!"}, "username"),
            ({"username": "john"}, "password"),
            ({}, "username"),
        ],
    )
    def test_missing_required_fields_return_400(
        self,
        api_client,
        url,
        payload,
        missing_field,
    ):
        response = api_client.post(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 400
        assert missing_field in response.data


@pytest.mark.django_db
class TestTokenRefreshView:
    """Tests for JWT token refresh endpoint."""

    @pytest.fixture
    def password(self):
        return "secure_pass_1234"

    @pytest.fixture
    def user(self):
        return UserFactory(
            username="john",
        )

    @pytest.fixture
    def obtain_url(self):
        return reverse("token_obtain_pair")

    @pytest.fixture
    def refresh_url(self):
        return reverse("token_refresh")

    @pytest.fixture
    def refresh_token(
        self,
        api_client,
        obtain_url,
        user,
        password,
    ):
        response = api_client.post(
            obtain_url,
            {
                "username": user.username,
                "password": password,
            },
            format="json",
        )

        assert response.status_code == 200

        return response.data["refresh"]

    # ------------------------------------------------------------------
    # Success
    # ------------------------------------------------------------------

    def test_can_refresh_access_token(
        self,
        api_client,
        refresh_url,
        refresh_token,
    ):
        response = api_client.post(
            refresh_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        assert response.status_code == 200

        assert "access" in response.data
        assert isinstance(response.data["access"], str)

    # ------------------------------------------------------------------
    # Invalid token
    # ------------------------------------------------------------------

    def test_invalid_refresh_token_returns_401(
        self,
        api_client,
        refresh_url,
    ):
        response = api_client.post(
            refresh_url,
            {
                "refresh": "invalid.token",
            },
            format="json",
        )

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # Missing token
    # ------------------------------------------------------------------

    def test_missing_refresh_token_returns_400(
        self,
        api_client,
        refresh_url,
    ):
        response = api_client.post(
            refresh_url,
            {},
            format="json",
        )

        assert response.status_code == 400
        assert "refresh" in response.data

    # ------------------------------------------------------------------
    # Malformed token
    # ------------------------------------------------------------------

    def test_malformed_refresh_token_returns_401(
        self,
        api_client,
        refresh_url,
    ):
        response = api_client.post(
            refresh_url,
            {
                "refresh": "not-a-jwt-token",
            },
            format="json",
        )

        assert response.status_code == 401