from unittest.mock import patch
import pytest

from django.urls import reverse

from board.models import BoardMembership
from .conftest import (
    UserFactory,
    BoardFactory,
    BoardListFactory,
    CardFactory,
    BoardMembershipFactory
)

#======================
#  Start GuestBoardListView Tests
#======================

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




#======================
#  End GuestBoardListView Tests
#======================




#======================
#  Start UserRetrieveView Tests
#======================

@pytest.mark.django_db
class TestUserRetrieveView:
    """Tests for UserRetrieveView."""

    @pytest.fixture
    def url(self):
        return reverse("user")

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_profile(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    def test_authenticated_user_can_retrieve_own_profile(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == user.id
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email

    # ---------------------------------------------------------
    # Always returns authenticated user
    # ---------------------------------------------------------

    def test_returns_authenticated_user_not_another_user(
        self,
        api_client,
        user,
        url,
    ):
        other_user = UserFactory()

        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == user.id
        assert response.data["username"] == user.username

        assert response.data["id"] != other_user.id
        assert response.data["username"] != other_user.username

#======================
#  End UserRetrieveView Tests
#======================


#======================
#  Start SearchBoardView Tests
#======================


@pytest.mark.django_db
class TestSearchBoardView:
    """Tests for SearchBoardView."""

    @pytest.fixture
    def url(self):
        return reverse("search_boards")

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_search_boards(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url, {"search": "project"})

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    def test_returns_owned_and_member_boards_matching_search(
        self,
        api_client,
        user,
        url,
    ):
        owned_board = BoardFactory(
            owner=user,
            name="Project Alpha",
        )

        member_board = BoardFactory(
            name="Project Beta",
        )

        BoardMembership.objects.create(
            board=member_board,
            user=user,
            member_type="member",
            accepted=True,
        )

        BoardFactory(
            owner=user,
            name="Shopping List",
        )

        inaccessible_board = BoardFactory(
            name="Project Secret",
        )

        api_client.force_authenticate(user)

        response = api_client.get(
            url,
            {"search": "Project"},
        )

        assert response.status_code == 200
        assert len(response.data) == 2

        ids = {board["id"] for board in response.data}

        assert owned_board.id in ids
        assert member_board.id in ids
        assert inaccessible_board.id not in ids

    # ---------------------------------------------------------
    # Case-insensitive search
    # ---------------------------------------------------------

    def test_search_is_case_insensitive(
        self,
        api_client,
        user,
        url,
    ):
        board = BoardFactory(
            owner=user,
            name="My Awesome Project",
        )

        api_client.force_authenticate(user)

        response = api_client.get(
            url,
            {"search": "awesome"},
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == board.id

    # ---------------------------------------------------------
    # No matches
    # ---------------------------------------------------------

    def test_returns_empty_list_when_no_board_matches(
        self,
        api_client,
        user,
        url,
    ):
        BoardFactory(
            owner=user,
            name="Project Alpha",
        )

        api_client.force_authenticate(user)

        response = api_client.get(
            url,
            {"search": "Finance"},
        )

        assert response.status_code == 200
        assert response.data == []

    # ---------------------------------------------------------
    # Access filtering
    # ---------------------------------------------------------

    def test_matching_board_without_access_is_not_returned(
        self,
        api_client,
        user,
        url,
    ):
        BoardFactory(
            name="Project Alpha",
        )

        api_client.force_authenticate(user)

        response = api_client.get(
            url,
            {"search": "Project"},
        )

        assert response.status_code == 200
        assert response.data == []

    # ---------------------------------------------------------
    # Missing query parameter
    # ---------------------------------------------------------

    def test_missing_search_parameter_returns_server_error(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        with pytest.raises(KeyError):
            api_client.get(url)

#======================
#  End SearchBoardView Tests
#======================


#======================
#  Start SearchCardView Tests
#======================

@pytest.mark.django_db
class TestSearchCardView:
    """Tests for SearchCardView."""

    @pytest.fixture
    def url(self):
        return reverse("search_cards")

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_search_cards(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url, {"search": "task"})

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    def test_returns_owned_and_member_cards_matching_search(
        self,
        api_client,
        user,
        url,
    ):
        # Owned board
        owned_board = BoardFactory(owner=user)
        owned_list = BoardListFactory(board=owned_board)
        owned_card = CardFactory(
            board_list=owned_list,
            name="Project Alpha",
        )

        # Member board
        member_board = BoardFactory()
        BoardMembership.objects.create(
            board=member_board,
            user=user,
            member_type="member",
            accepted=True,
        )
        member_list = BoardListFactory(board=member_board)
        member_card = CardFactory(
            board_list=member_list,
            name="Project Beta",
        )

        # Accessible but doesn't match search
        other_card = CardFactory(
            board_list=owned_list,
            name="Shopping List",
        )

        # Inaccessible board
        private_board = BoardFactory()
        private_list = BoardListFactory(board=private_board)
        private_card = CardFactory(
            board_list=private_list,
            name="Project Secret",
        )

        api_client.force_authenticate(user)

        response = api_client.get(
            url,
            {"search": "Project"},
        )

        assert response.status_code == 200
        assert len(response.data) == 2

        ids = {card["id"] for card in response.data}

        assert owned_card.id in ids
        assert member_card.id in ids
        assert other_card.id not in ids
        assert private_card.id not in ids

    # ---------------------------------------------------------
    # Case-insensitive search
    # ---------------------------------------------------------

    def test_search_is_case_insensitive(
        self,
        api_client,
        user,
        url,
    ):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)

        card = CardFactory(
            board_list=board_list,
            name="My Awesome Task",
        )

        api_client.force_authenticate(user)

        response = api_client.get(
            url,
            {"search": "awesome"},
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == card.id

    # ---------------------------------------------------------
    # Empty result
    # ---------------------------------------------------------

    def test_returns_empty_list_when_no_card_matches(
        self,
        api_client,
        user,
        url,
    ):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)

        CardFactory(
            board_list=board_list,
            name="Project Alpha",
        )

        api_client.force_authenticate(user)

        response = api_client.get(
            url,
            {"search": "Finance"},
        )

        assert response.status_code == 200
        assert response.data == []

    # ---------------------------------------------------------
    # Access filtering
    # ---------------------------------------------------------

    def test_matching_card_without_access_is_not_returned(
        self,
        api_client,
        user,
        url,
    ):
        board = BoardFactory()
        board_list = BoardListFactory(board=board)

        CardFactory(
            board_list=board_list,
            name="Project Alpha",
        )

        api_client.force_authenticate(user)

        response = api_client.get(
            url,
            {"search": "Project"},
        )

        assert response.status_code == 200
        assert response.data == []

    # ---------------------------------------------------------
    # Missing query parameter
    # ---------------------------------------------------------

    def test_missing_search_parameter_raises_key_error(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        with pytest.raises(KeyError):
            api_client.get(url)
#======================
#  End SearchCardView Tests
#======================


#======================
#  Start ClosedBoardView Tests
#======================


@pytest.mark.django_db
class TestClosedBoardView:
    """Tests for ClosedBoardView."""

    @pytest.fixture
    def url(self):
        return reverse("closed_boards")

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_closed_boards(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    def test_returns_only_closed_boards_owned_by_user(
        self,
        api_client,
        user,
        url,
    ):
        closed_board_1 = BoardFactory(
            owner=user,
            closed=True,
        )

        closed_board_2 = BoardFactory(
            owner=user,
            closed=True,
        )

        open_board = BoardFactory(
            owner=user,
            closed=False,
        )

        other_users_closed_board = BoardFactory(
            owner=UserFactory(),
            closed=True,
        )

        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 2

        ids = {board["id"] for board in response.data}

        assert closed_board_1.id in ids
        assert closed_board_2.id in ids
        assert open_board.id not in ids
        assert other_users_closed_board.id not in ids

    # ---------------------------------------------------------
    # Empty queryset
    # ---------------------------------------------------------

    def test_returns_empty_list_when_user_has_no_closed_boards(
        self,
        api_client,
        user,
        url,
    ):
        BoardFactory(
            owner=user,
            closed=False,
        )

        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == []

    # ---------------------------------------------------------
    # Only owner's boards are returned
    # ---------------------------------------------------------

    def test_closed_boards_of_other_users_are_not_returned(
        self,
        api_client,
        user,
        url,
    ):
        BoardFactory(
            owner=UserFactory(),
            closed=True,
        )

        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == []

#======================
#  End ClosedBoardView Tests
#======================


#======================
#  Start BoardRetrieveView Tests
#======================

@pytest.mark.django_db
class TestBoardRetrieveView:
    """Tests for BoardRetrieveView."""

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def board(self, owner):
        return BoardFactory(
            owner=owner,
            closed=False,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_board(
        self,
        api_client,
        board,
    ):
        url = reverse("board", args=[board.pk])

        response = api_client.get(url)

        # Adjust to 401 if your project uses Basic/Token authentication.
        assert response.status_code == 401

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    def test_owner_can_retrieve_board(
        self,
        api_client,
        owner,
        board,
    ):
        api_client.force_authenticate(owner)

        url = reverse("board", args=[board.pk])

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == board.id
        assert response.data["name"] == board.name

    def test_board_member_can_retrieve_board(
        self,
        api_client,
        user,
        board,
    ):
        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        api_client.force_authenticate(user)

        url = reverse("board", args=[board.pk])

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == board.id

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_unrelated_user_gets_404(
        self,
        api_client,
        board,
    ):
        outsider = UserFactory()

        api_client.force_authenticate(outsider)

        url = reverse("board", args=[board.pk])

        response = api_client.get(url)

        assert response.status_code == 404

    def test_closed_board_is_not_retrievable_by_owner(
        self,
        api_client,
        owner,
    ):
        board = BoardFactory(
            owner=owner,
            closed=True,
        )

        api_client.force_authenticate(owner)

        url = reverse("board", args=[board.pk])

        response = api_client.get(url)

        assert response.status_code == 404

    def test_closed_board_is_not_retrievable_by_member(
        self,
        api_client,
        user,
    ):
        board = BoardFactory(closed=True)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        api_client.force_authenticate(user)

        url = reverse("board", args=[board.pk])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_nonexistent_board_returns_404(
        self,
        api_client,
        owner,
    ):
        api_client.force_authenticate(owner)

        url = reverse("board", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404
#======================
#  End BoardRetrieveView Tests
#======================



#======================
#  Start CurrentUser Tests
#======================


@pytest.mark.django_db
class TestCurrentUserView:
    """Tests for CurrentUser API view."""

    @pytest.fixture
    def url(self):
        return reverse("current_user")

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_access_current_user(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    def test_authenticated_user_receives_own_user_id(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            "user": user.id,
        }

    # ---------------------------------------------------------
    # Always returns authenticated user
    # ---------------------------------------------------------

    def test_returns_authenticated_user_not_another_user(
        self,
        api_client,
        user,
        url,
    ):
        other_user = UserFactory()

        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["user"] == user.id
        assert response.data["user"] != other_user.id
#======================
#  End CurrentUser Tests
#======================

#======================
#  Start BoardListOrderUpdating Tests
#======================


@pytest.mark.django_db
class TestBoardListOrderUpdatingView:
    """Tests for BoardListOrderUpdating."""

    @pytest.fixture
    def url(self):
        return reverse("update_list_order")

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def board(self, owner):
        return BoardFactory(owner=owner)

    @pytest.fixture
    def board_lists(self, board):
        return [
            BoardListFactory(board=board, order=1),
            BoardListFactory(board=board, order=2),
            BoardListFactory(board=board, order=3),
        ]

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_anonymous_user_cannot_update_board_list_order(
        self,
        api_client,
        url,
        board_lists,
    ):
        response = api_client.patch(
            url,
            [{"id": board_lists[0].id, "order": 10}],
            format="json",
        )

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # Success (Owner)
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_update_board_list_order(
        self,
        mock_log,
        api_client,
        owner,
        board,
        board_lists,
        url,
    ):
        api_client.force_authenticate(owner)

        payload = [
            {"id": board_lists[0].id, "order": 3},
            {"id": board_lists[1].id, "order": 1},
            {"id": board_lists[2].id, "order": 2},
        ]

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 200

        for obj, expected_order in zip(board_lists, [3, 1, 2]):
            obj.refresh_from_db()
            assert obj.order == expected_order

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == owner
        assert kwargs["user"] == owner
        assert kwargs["board"] == board
        assert kwargs["board_list"] is None
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "change_lists_order"
        assert kwargs["text"] == "Lists order changed"

    # ------------------------------------------------------------------
    # Success (Board member)
    # ------------------------------------------------------------------

    def test_board_member_can_update_board_list_order(
        self,
        api_client,
        user,
        board,
        board_lists,
        url,
    ):
        BoardMembershipFactory(
            board=board,
            user=user,
        )

        api_client.force_authenticate(user)

        payload = [
            {"id": board_lists[0].id, "order": 100},
            {"id": board_lists[1].id, "order": 200},
        ]

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 200

        board_lists[0].refresh_from_db()
        board_lists[1].refresh_from_db()

        assert board_lists[0].order == 100
        assert board_lists[1].order == 200

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    def test_user_cannot_update_other_users_board_lists(
        self,
        api_client,
        user,
        board_lists,
        url,
    ):
        api_client.force_authenticate(user)

        payload = [
            {"id": board_lists[0].id, "order": 10},
        ]

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 404

        board_lists[0].refresh_from_db()
        assert board_lists[0].order == 1

    def test_nonexistent_board_list_returns_404(
        self,
        api_client,
        owner,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            [
                {
                    "id": 999999,
                    "order": 1,
                }
            ],
            format="json",
        )

        assert response.status_code == 404

    def test_mixed_accessible_and_inaccessible_board_lists_returns_404(
        self,
        api_client,
        owner,
        board_lists,
        url,
    ):
        other_board = BoardFactory()
        other_list = BoardListFactory(
            board=other_board,
            order=50,
        )

        api_client.force_authenticate(owner)

        payload = [
            {
                "id": board_lists[0].id,
                "order": 10,
            },
            {
                "id": other_list.id,
                "order": 20,
            },
        ]

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 404

        board_lists[0].refresh_from_db()
        other_list.refresh_from_db()

        assert board_lists[0].order == 1
        assert other_list.order == 50

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_invalid_order_returns_400(
        self,
        api_client,
        owner,
        board_lists,
        url,
    ):
        api_client.force_authenticate(owner)

        payload = [
            {
                "id": board_lists[0].id,
                "order": "invalid",
            }
        ]

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 400

        board_lists[0].refresh_from_db()
        assert board_lists[0].order == 1


#======================
#  End BoardListOrderUpdating Tests
#======================