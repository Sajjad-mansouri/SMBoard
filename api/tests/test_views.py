import pytest

from django.urls import reverse

from board.models import BoardMembership
from .conftest import (
    UserFactory,
    BoardFactory,
)


@pytest.mark.django_db
class TestGuestBoardListView:
    """Tests for GuestBoardListView."""

    @pytest.fixture
    def url(self):
        return reverse("guest_boards")

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_guest_boards(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    def test_returns_only_guest_boards(
        self,
        api_client,
        user,
        url,
    ):
        # Board where user is a member (should appear)
        guest_board = BoardFactory(closed=False)

        BoardMembership.objects.create(
            board=guest_board,
            user=user,
            member_type="member",
            accepted=True,
        )

        # User owns this board (should NOT appear)
        owned_board = BoardFactory(
            owner=user,
            closed=False,
        )

        # User is member but board is closed (should NOT appear)
        closed_board = BoardFactory(closed=True)

        BoardMembership.objects.create(
            board=closed_board,
            user=user,
            member_type="member",
            accepted=True,
        )

        # Unrelated board (should NOT appear)
        BoardFactory(closed=False)

        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1

        assert response.data[0]["id"] == guest_board.id

    # ---------------------------------------------------------
    # Empty queryset
    # ---------------------------------------------------------

    def test_returns_empty_list_when_user_has_no_guest_boards(
        self,
        api_client,
        user,
        url,
    ):
        BoardFactory(owner=user)

        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == []

