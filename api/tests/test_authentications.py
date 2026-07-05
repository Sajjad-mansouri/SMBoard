import pytest
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

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


@pytest.mark.django_db
class TestTokenVerifyView:
    """Tests for JWT token verification endpoint."""

    @pytest.fixture
    def password(self):
        return "secure_pass_1234"

    @pytest.fixture
    def user(self):
        return UserFactory(username="john")

    @pytest.fixture
    def obtain_url(self):
        return reverse("token_obtain_pair")

    @pytest.fixture
    def verify_url(self):
        return reverse("token_verify")

    @pytest.fixture
    def tokens(
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

        return response.data

    # ------------------------------------------------------------------
    # Success
    # ------------------------------------------------------------------

    def test_valid_access_token_can_be_verified(
        self,
        api_client,
        verify_url,
        tokens,
    ):
        response = api_client.post(
            verify_url,
            {
                "token": tokens["access"],
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data == {}

    def test_valid_refresh_token_can_be_verified(
        self,
        api_client,
        verify_url,
        tokens,
    ):
        response = api_client.post(
            verify_url,
            {
                "token": tokens["refresh"],
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data == {}

    # ------------------------------------------------------------------
    # Invalid token
    # ------------------------------------------------------------------

    def test_invalid_token_returns_401(
        self,
        api_client,
        verify_url,
    ):
        response = api_client.post(
            verify_url,
            {
                "token": "invalid.token",
            },
            format="json",
        )

        assert response.status_code == 401

    def test_malformed_token_returns_401(
        self,
        api_client,
        verify_url,
    ):
        response = api_client.post(
            verify_url,
            {
                "token": "not-a-jwt",
            },
            format="json",
        )

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_missing_token_returns_400(
        self,
        api_client,
        verify_url,
    ):
        response = api_client.post(
            verify_url,
            {},
            format="json",
        )

        assert response.status_code == 400
        assert "token" in response.data



@pytest.mark.django_db
class TestLoginApiView:
    """Tests for LoginApiView."""

    @pytest.fixture
    def url(self):
        return reverse("login")

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

    def test_user_can_login(
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

        access = response.data["access"]
        refresh = response.data["refresh"]

        # Response contains expected fields
        assert set(response.data.keys()) == {"access", "refresh"}

        # Tokens are strings
        assert isinstance(access, str)
        assert isinstance(refresh, str)

        # Tokens are valid JWTs
        access_token = AccessToken(access)
        refresh_token = RefreshToken(refresh)

        # Tokens belong to the authenticated user
        assert int(access_token["user_id"]) == user.id
        assert int(refresh_token["user_id"]) == user.id

        # Refresh token can generate an access token
        assert str(refresh_token.access_token)

    # ------------------------------------------------------------------
    # Invalid credentials
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
                "password": "wrong_password",
            },
            format="json",
        )

        assert response.status_code == 401
        assert response.data == {"error": "Invalid Credentials"}

    def test_unknown_username_returns_401(
        self,
        api_client,
        url,
        password,
    ):
        response = api_client.post(
            url,
            {
                "username": "unknown_user",
                "password": password,
            },
            format="json",
        )

        assert response.status_code == 401
        assert response.data == {"error": "Invalid Credentials"}

    # ------------------------------------------------------------------
    # Missing credentials
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "payload",
        [
            {"password": "secure_pass_1234"},
            {"username": "john"},
            {},
        ],
    )
    def test_missing_credentials_return_401(
        self,
        api_client,
        url,
        payload,
    ):
        response = api_client.post(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 401
        assert response.data == {"error": "Invalid Credentials"}

    # ------------------------------------------------------------------
    # Inactive user
    # ------------------------------------------------------------------

    def test_inactive_user_cannot_login(
        self,
        api_client,
        url,
        user,
        password,
    ):
        user.is_active = False
        user.save(update_fields=["is_active"])

        response = api_client.post(
            url,
            {
                "username": user.username,
                "password": password,
            },
            format="json",
        )

        assert response.status_code == 401
        assert response.data == {"error": "Invalid Credentials"}





@pytest.mark.django_db
class TestLogoutApiView:
    """Tests for LogoutApiView."""

    @pytest.fixture
    def password(self):
        return "secure_pass_1234"

    @pytest.fixture
    def user(self):
        return UserFactory(username="john")

    @pytest.fixture
    def login_url(self):
        return reverse("login")

    @pytest.fixture
    def logout_url(self):
        return reverse("logout")

    @pytest.fixture
    def refresh_token(
        self,
        api_client,
        login_url,
        user,
        password,
    ):
        response = api_client.post(
            login_url,
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

    def test_user_can_logout(
        self,
        api_client,
        logout_url,
        refresh_token,
    ):
        response = api_client.post(
            logout_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data == {
            "message": "Successfuly logged out"
        }

    # ------------------------------------------------------------------
    # Missing refresh token
    # ------------------------------------------------------------------

    def test_missing_refresh_token_returns_400(
        self,
        api_client,
        logout_url,
    ):
        response = api_client.post(
            logout_url,
            {},
            format="json",
        )

        assert response.status_code == 400
        assert response.data == {
            "error": "Logout failed"
        }

    # ------------------------------------------------------------------
    # Invalid refresh token
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "token",
        [
            "invalid.token",
            "not-a-jwt",
            "",
        ],
    )
    def test_invalid_refresh_token_returns_400(
        self,
        api_client,
        logout_url,
        token,
    ):
        response = api_client.post(
            logout_url,
            {
                "refresh": token,
            },
            format="json",
        )

        assert response.status_code == 400
        assert response.data == {
            "error": "Logout failed"
        }

    # ------------------------------------------------------------------
    # Blacklisting
    # ------------------------------------------------------------------

    def test_refresh_token_is_blacklisted_after_logout(
        self,
        api_client,
        logout_url,
        refresh_token,
    ):
        response = api_client.post(
            logout_url,
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        assert response.status_code == 200

        with pytest.raises(TokenError):
            RefreshToken(refresh_token).blacklist()