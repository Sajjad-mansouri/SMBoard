from unittest.mock import patch
import pytest

from django.urls import reverse
from board.models import BoardMembership, BoardWatch, CardWatch, Card
from .conftest import (
    UserFactory,
    BoardFactory,
    BoardListFactory,
    CardFactory,
    BoardMembershipFactory,
    BoardWatchFactory,
    CardWatchFactory
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


#======================
#  Start CardOrderUpdating Tests
#======================


@pytest.mark.django_db
class TestCardOrderUpdatingView:
    """Tests for CardOrderUpdating."""

    @pytest.fixture
    def url(self):
        return reverse("card_order")

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def board(self, owner):
        return BoardFactory(owner=owner)

    @pytest.fixture
    def board_list(self, board):
        return BoardListFactory(board=board)

    @pytest.fixture
    def cards(self, board_list):
        return [
            CardFactory(board_list=board_list, order=1),
            CardFactory(board_list=board_list, order=2),
            CardFactory(board_list=board_list, order=3),
        ]

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_card_order(
        self,
        api_client,
        url,
        cards,
    ):
        response = api_client.patch(
            url,
            [{"id": cards[0].id, "order": 5}],
            format="json",
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_update_card_order(
        self,
        mock_log,
        api_client,
        owner,
        board,
        board_list,
        cards,
        url,
    ):
        api_client.force_authenticate(owner)

        payload = [
            {"id": cards[0].id, "order": 3},
            {"id": cards[1].id, "order": 1},
            {"id": cards[2].id, "order": 2},
        ]

        response = api_client.patch(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 200

        for card, expected in zip(cards, [3, 1, 2]):
            card.refresh_from_db()
            assert card.order == expected

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == owner
        assert kwargs["user"] == owner
        assert kwargs["board"] == board
        assert kwargs["board_list"] == board_list
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "change_cards_order"
        assert kwargs["text"] == (
            f"Cards of '{board_list.name}' list, order changed"
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_update_card_order(
        self,
        api_client,
        user,
        board,
        cards,
        url,
    ):
        BoardMembershipFactory(
            board=board,
            user=user,
        )

        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            [
                {"id": cards[0].id, "order": 10},
                {"id": cards[1].id, "order": 20},
            ],
            format="json",
        )

        assert response.status_code == 200

        cards[0].refresh_from_db()
        cards[1].refresh_from_db()

        assert cards[0].order == 10
        assert cards[1].order == 20

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_update_other_users_cards(
        self,
        api_client,
        user,
        cards,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            [{"id": cards[0].id, "order": 99}],
            format="json",
        )

        assert response.status_code == 404

        cards[0].refresh_from_db()
        assert cards[0].order == 1

    def test_nonexistent_card_returns_404(
        self,
        api_client,
        owner,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            [{"id": 999999, "order": 1}],
            format="json",
        )

        assert response.status_code == 404

    def test_mixed_accessible_and_inaccessible_cards_returns_404(
        self,
        api_client,
        owner,
        cards,
        url,
    ):
        other_board = BoardFactory()
        other_list = BoardListFactory(board=other_board)
        other_card = CardFactory(
            board_list=other_list,
            order=50,
        )

        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            [
                {"id": cards[0].id, "order": 10},
                {"id": other_card.id, "order": 20},
            ],
            format="json",
        )

        assert response.status_code == 404

        cards[0].refresh_from_db()
        other_card.refresh_from_db()

        assert cards[0].order == 1
        assert other_card.order == 50

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_invalid_order_returns_400(
        self,
        api_client,
        owner,
        cards,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            [{"id": cards[0].id, "order": "invalid"}],
            format="json",
        )

        assert response.status_code == 400

        cards[0].refresh_from_db()
        assert cards[0].order == 1
#======================
#  End CardOrderUpdating Tests
#======================


#======================
#  Start BoardWatchView Tests
#======================



@pytest.mark.django_db
class TestBoardWatchView:
    """Tests for BoardWatchView."""

    @pytest.fixture
    def url(self):
        return reverse("board_watch")

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def board(self, owner):
        return BoardFactory(owner=owner)

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_toggle_board_watch(
        self,
        api_client,
        board,
        url,
    ):
        response = api_client.post(
            url,
            {
                "board": board.id,
                "watch": True,
            },
            format="json",
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Watch
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_user_can_watch_board(
        self,
        mock_log,
        api_client,
        owner,
        board,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "board": board.id,
                "watch": True,
            },
            format="json",
        )

        assert response.status_code == 200

        board_watch = BoardWatch.objects.get(
            user=owner,
            board=board,
        )

        assert board_watch.watch is True

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == owner
        assert kwargs["user"] == owner
        assert kwargs["board"] == board
        assert kwargs["board_list"] is None
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "watch_board"
        assert kwargs["text"] == (
            f"{board.name} Board started being watched"
        )

    # ---------------------------------------------------------
    # Unwatch
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_user_can_unwatch_board(
        self,
        mock_log,
        api_client,
        owner,
        board,
        url,
    ):
        BoardWatchFactory(
            user=owner,
            board=board,
            watch=True,
        )

        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "board": board.id,
                "watch": False,
            },
            format="json",
        )

        assert response.status_code == 200

        board_watch = BoardWatch.objects.get(
            user=owner,
            board=board,
        )

        assert board_watch.watch is False

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "unwatch_board"
        assert kwargs["text"] == (
            f"{board.name} Board stopped being watched"
        )

    # ---------------------------------------------------------
    # Update existing watch object
    # ---------------------------------------------------------

    def test_existing_board_watch_is_updated_not_recreated(
        self,
        api_client,
        owner,
        board,
        url,
    ):
        board_watch = BoardWatchFactory(
            user=owner,
            board=board,
            watch=False,
        )

        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "board": board.id,
                "watch": True,
            },
            format="json",
        )

        assert response.status_code == 200

        assert BoardWatch.objects.filter(
            user=owner,
            board=board,
        ).count() == 1

        board_watch.refresh_from_db()

        assert board_watch.watch is True

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_invalid_data_returns_400(
        self,
        api_client,
        owner,
        board,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "board": board.id,
                "watch": "invalid",
            },
            format="json",
        )

        assert response.status_code == 400
#======================
#  End BoardWatchView Tests
#======================


#======================
#  Start CardWatchView Tests
#======================

@pytest.mark.django_db
class TestCardWatchView:

    @pytest.fixture
    def url(self):
        return reverse("card_watch")

    @pytest.fixture
    def user(self):
        return UserFactory()


    @pytest.fixture
    def board(self, user):
        return BoardFactory(owner=user)

    @pytest.fixture
    def board_list(self, board):
        return BoardListFactory(board=board)

    @pytest.fixture
    def card(self, board_list):
        return CardFactory(board_list=board_list)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_anonymous_user_cannot_toggle_card_watch(
        self,
        api_client,
        card,
        url,
    ):
        response = api_client.post(
            url,
            {
                "card": card.id,
                "watch": True,
            },
            format="json",
        )

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # Watch
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_user_can_watch_card(
        self,
        mock_log,
        api_client,
        user,
        card,
        url,
    ):
        print("user", user)
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "watch": True,
            },
            format="json",
        )

        assert response.status_code == 200

        card_watch = CardWatch.objects.get(
            user=user,
            card=card,
        )

        assert card_watch.watch is True

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == card.board_list.board
        assert kwargs["board_list"] == card.board_list
        assert kwargs["card"] == card
        assert kwargs["action_type"] == "watch_card"
        assert kwargs["text"] == (
            f"{card.name} Card started being watched"
        )

    # ------------------------------------------------------------------
    # Unwatch
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_user_can_unwatch_card(
        self,
        mock_log,
        api_client,
        user,
        card,
        url,
    ):
        CardWatchFactory(
            user=user,
            card=card,
            watch=True,
        )

        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "watch": False,
            },
            format="json",
        )

        assert response.status_code == 200

        card_watch = CardWatch.objects.get(
            user=user,
            card=card,
        )

        assert card_watch.watch is False

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "unwatch_card"
        assert kwargs["text"] == (
            f"{card.name} Card stopped being watched"
        )

    # ------------------------------------------------------------------
    # Existing object is updated
    # ------------------------------------------------------------------

    def test_existing_card_watch_is_updated_not_recreated(
        self,
        api_client,
        user,
        card,
        url,
    ):
        card_watch = CardWatchFactory(
            user=user,
            card=card,
            watch=False,
        )

        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "watch": True,
            },
            format="json",
        )

        assert response.status_code == 200

        assert CardWatch.objects.filter(
            user=user,
            card=card,
        ).count() == 1

        card_watch.refresh_from_db()

        assert card_watch.watch is True

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_invalid_watch_value_returns_400(
        self,
        api_client,
        user,
        card,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "watch": "invalid",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_missing_card_returns_403(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "watch": True,
            },
            format="json",
        )

        assert response.status_code == 403
#======================
#  End CardWatchView Tests
#======================

#======================
#  Start CopyCardView Tests
#======================



@pytest.mark.django_db
class TestCopyCardView:
    """Tests for CopyCardView."""

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def member(self):
        return UserFactory()

    @pytest.fixture
    def stranger(self):
        return UserFactory()

    @pytest.fixture
    def board(self, owner):
        return BoardFactory(owner=owner)

    @pytest.fixture
    def board_list(self, board):
        return BoardListFactory(board=board)

    @pytest.fixture
    def card(self, board_list):
        return CardFactory(
            board_list=board_list,
            name="Original Card",
        )

    @pytest.fixture
    def member_membership(self, board, member):
        return BoardMembershipFactory(
            board=board,
            user=member,
        )

    @pytest.fixture
    def url(self, card):
        return reverse("copy_card", args=[card.pk])

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_anonymous_user_cannot_copy_card(
        self,
        api_client,
        url,
    ):
        response = api_client.post(url)

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # Success (owner)
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_copy_card(
        self,
        mock_log,
        api_client,
        owner,
        board,
        board_list,
        card,
        url,
    ):
        api_client.force_authenticate(owner)

        original_pk = card.pk

        response = api_client.post(url)

        assert response.status_code == 200

        assert Card.objects.count() == 2

        copied_card = Card.objects.exclude(pk=original_pk).get()

        assert copied_card.pk != original_pk
        assert copied_card.name == card.name
        assert copied_card.board_list == card.board_list

        assert response.data["id"] == copied_card.id
        assert response.data["name"] == copied_card.name

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == owner
        assert kwargs["user"] == owner
        assert kwargs["board"] == board
        assert kwargs["board_list"] == board_list
        assert kwargs["card"] == copied_card
        assert kwargs["action_type"] == "copy_card"
        assert kwargs["text"] == (
            f"The '{copied_card.name}' card copied "
        )

    # ------------------------------------------------------------------
    # Success (board member)
    # ------------------------------------------------------------------

    def test_board_member_can_copy_card(
        self,
        api_client,
        member,
        member_membership,
        card,
        url,
    ):
        api_client.force_authenticate(member)

        response = api_client.post(url)

        assert response.status_code == 200

        assert Card.objects.filter(
            name=card.name,
            board_list=card.board_list,
        ).count() == 2

    # ------------------------------------------------------------------
    # Permission
    # ------------------------------------------------------------------

    def test_user_cannot_copy_card_from_other_board(
        self,
        api_client,
        stranger,
        url,
    ):
        api_client.force_authenticate(stranger)

        response = api_client.post(url)

        assert response.status_code == 404

#======================
#  End CopyCardView Tests
#======================


#======================
#  Start CardArchivedUpdateView Tests
#======================


@pytest.mark.django_db
class TestCardArchivedUpdateView:
    """Tests for CardArchivedUpdateView."""

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def stranger(self):
        return UserFactory()

    @pytest.fixture
    def board(self, owner):
        return BoardFactory(owner=owner)

    @pytest.fixture
    def board_list(self, board):
        return BoardListFactory(board=board)

    @pytest.fixture
    def card(self, board_list):
        return CardFactory(
            board_list=board_list,
            archived=False,
        )

    @pytest.fixture
    def archived_card(self, board_list):
        return CardFactory(
            board_list=board_list,
            archived=True,
        )

    @pytest.fixture
    def url(self, card):
        return reverse("archive_card", args=[card.pk])

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_card_archive(
        self,
        api_client,
        url,
    ):
        response = api_client.patch(
            url,
            {"archived": True},
            format="json",
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Archive
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_archive_card(
        self,
        mock_log,
        api_client,
        owner,
        board,
        board_list,
        card,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            {"archived": True},
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()
        assert card.archived is True

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == owner
        assert kwargs["user"] == owner
        assert kwargs["board"] == board
        assert kwargs["board_list"] == board_list
        assert kwargs["card"] == card
        assert kwargs["action_type"] == "archive_card"
        assert kwargs["text"] == f"The '{card.name}' card was archived"

    # ---------------------------------------------------------
    # Unarchive
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_unarchive_card(
        self,
        mock_log,
        api_client,
        owner,
        archived_card,
    ):
        api_client.force_authenticate(owner)

        url = reverse("archive_card", args=[archived_card.pk])

        response = api_client.patch(
            url,
            {"archived": False},
            format="json",
        )

        assert response.status_code == 200

        archived_card.refresh_from_db()
        assert archived_card.archived is False

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "unarchive_card"
        assert kwargs["text"] == (
            f"The '{archived_card.name}' card was unarchived"
        )

    # ---------------------------------------------------------
    # No change
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_no_activity_logged_when_archived_value_does_not_change(
        self,
        mock_log,
        api_client,
        owner,
        card,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            {"archived": False},
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()
        assert card.archived is False

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_non_owner_cannot_update_card_archive(
        self,
        api_client,
        stranger,
        url,
        card,
    ):
        api_client.force_authenticate(stranger)

        response = api_client.patch(
            url,
            {"archived": True},
            format="json",
        )

        assert response.status_code == 404

        card.refresh_from_db()
        assert card.archived is False

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_invalid_archived_value_returns_400(
        self,
        api_client,
        owner,
        url,
        card,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            {"archived": "invalid"},
            format="json",
        )

        assert response.status_code == 400

        card.refresh_from_db()
        assert card.archived is False
#======================
#  End CardArchivedUpdateView Tests
#======================

#======================
#  Start BoardListArchivedUpdateView Tests
#======================


@pytest.mark.django_db
class TestBoardListArchivedUpdateView:
    """Tests for BoardListArchivedUpdateView."""

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def stranger(self):
        return UserFactory()

    @pytest.fixture
    def board(self, owner):
        return BoardFactory(owner=owner)

    @pytest.fixture
    def board_list(self, board):
        return BoardListFactory(
            board=board,
            archived=False,
        )

    @pytest.fixture
    def archived_board_list(self, board):
        return BoardListFactory(
            board=board,
            archived=True,
        )

    @pytest.fixture
    def url(self, board_list):
        return reverse(
            "archive_list",
            args=[board_list.pk],
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_anonymous_user_cannot_update_archive_status(
        self,
        api_client,
        url,
    ):
        response = api_client.patch(
            url,
            {"archived": True},
            format="json",
        )

        assert response.status_code == 401

    # ------------------------------------------------------------------
    # Archive
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_archive_board_list(
        self,
        mock_log,
        api_client,
        owner,
        board,
        board_list,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            {"archived": True},
            format="json",
        )

        assert response.status_code == 200

        board_list.refresh_from_db()
        assert board_list.archived is True

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == owner
        assert kwargs["user"] == owner
        assert kwargs["board"] == board
        assert kwargs["board_list"] == board_list
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "archive_list"
        assert kwargs["text"] == (
            f"The '{board_list.name}' list was archived"
        )

    # ------------------------------------------------------------------
    # Unarchive
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_unarchive_board_list(
        self,
        mock_log,
        api_client,
        owner,
        archived_board_list,
    ):
        api_client.force_authenticate(owner)

        url = reverse(
            "archive_list",
            args=[archived_board_list.pk],
        )

        response = api_client.patch(
            url,
            {"archived": False},
            format="json",
        )

        assert response.status_code == 200

        archived_board_list.refresh_from_db()
        assert archived_board_list.archived is False

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "unarchive_list"
        assert kwargs["text"] == (
            f"The '{archived_board_list.name}' list was unarchived"
        )

    # ------------------------------------------------------------------
    # No change
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_no_activity_logged_when_archive_status_is_unchanged(
        self,
        mock_log,
        api_client,
        owner,
        board_list,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            {"archived": False},
            format="json",
        )

        assert response.status_code == 200

        board_list.refresh_from_db()
        assert board_list.archived is False

        mock_log.assert_not_called()

    # ------------------------------------------------------------------
    # Permission
    # ------------------------------------------------------------------

    def test_non_owner_cannot_update_archive_status(
        self,
        api_client,
        stranger,
        board_list,
        url,
    ):
        api_client.force_authenticate(stranger)

        response = api_client.patch(
            url,
            {"archived": True},
            format="json",
        )

        assert response.status_code == 404

        board_list.refresh_from_db()
        assert board_list.archived is False

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_invalid_archived_value_returns_400(
        self,
        api_client,
        owner,
        board_list,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.patch(
            url,
            {"archived": "invalid"},
            format="json",
        )

        assert response.status_code == 400

        board_list.refresh_from_db()
        assert board_list.archived is False
#======================
#  End BoardListArchivedUpdateView Tests
#======================


#======================
#  Start PublicBoardAddress Tests
#======================


@pytest.mark.django_db
class TestPublicBoardAddressView:
    """Tests for PublicBoardAddress."""

    @pytest.fixture
    def owner(self):
        return UserFactory()

    @pytest.fixture
    def stranger(self):
        return UserFactory()

    @pytest.fixture
    def public_board(self, owner):
        return BoardFactory(
            owner=owner,
            status="public",
        )

    @pytest.fixture
    def private_board(self, owner):
        return BoardFactory(
            owner=owner,
            status="private",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_get_public_board_address(
        self,
        api_client,
        public_board,
    ):
        url = reverse(
            "public_board_address",
            args=[public_board.pk],
        )

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    @patch("api.board.views.get_current_site_address")
    def test_owner_can_get_public_board_address(
        self,
        mock_site,
        api_client,
        owner,
        public_board,
    ):
        mock_site.return_value = (
            "example.com",
            "https://example.com",
        )

        api_client.force_authenticate(owner)

        url = reverse(
            "public_board_address",
            args=[public_board.pk],
        )

        response = api_client.get(url)

        assert response.status_code == 200

        expected = (
            f"https://example.com/public/"
            f"{public_board.short_uuid}/"
            f"{public_board.slug}/"
        )

        assert response.data == {
            "board_address": expected,
        }

        mock_site.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_non_owner_gets_404(
        self,
        api_client,
        stranger,
        public_board,
    ):
        api_client.force_authenticate(stranger)

        url = reverse(
            "public_board_address",
            args=[public_board.pk],
        )

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Private board
    # ---------------------------------------------------------

    def test_private_board_returns_404(
        self,
        api_client,
        owner,
        private_board,
    ):
        api_client.force_authenticate(owner)

        url = reverse(
            "public_board_address",
            args=[private_board.pk],
        )

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Nonexistent board
    # ---------------------------------------------------------

    def test_nonexistent_board_returns_404(
        self,
        api_client,
        owner,
    ):
        api_client.force_authenticate(owner)

        url = reverse(
            "public_board_address",
            args=[999999],
        )

        response = api_client.get(url)

        assert response.status_code == 404
#======================
#  End PublicBoardAddress Tests
#======================
