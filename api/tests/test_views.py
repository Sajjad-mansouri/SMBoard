import pytest
from django.db.utils import IntegrityError
from django.urls import reverse
from unittest.mock import call, patch
from .conftest import BoardFactory, UserFactory, BoardListFactory, CardFactory, CheckListFactory
from board.models import Board, BoardMembership, Card, CheckList


#======================
#  Start BoardViewSet Tests
#======================


@pytest.mark.django_db
class TestBoardListView:
    """Tests for BoardViewSet list endpoint."""

    @pytest.fixture
    def url(self):
        # Change "board-list" if your router basename is different.
        return reverse("board-list")

    @pytest.fixture
    def user_boards(self, user):
        return [
            BoardFactory(owner=user, name="Board 1"),
            BoardFactory(owner=user, name="Board 2"),
            BoardFactory(owner=user, name="Board 3"),
        ]

    @pytest.fixture
    def another_user_boards(self, another_user):
        return [
            BoardFactory(owner=another_user, name="Private 1"),
            BoardFactory(owner=another_user, name="Private 2"),
        ]

    def test_list_returns_200(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(url)

        assert response.status_code == 200

    def test_returns_only_authenticated_user_boards(
        self,
        api_client,
        user,
        url,
        user_boards,
        another_user_boards,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == len(user_boards)

        returned_ids = {board["id"] for board in response.data}
        expected_ids = {board.id for board in user_boards}

        assert returned_ids == expected_ids

    def test_does_not_return_other_users_boards(
        self,
        api_client,
        user,
        url,
        user_boards,
        another_user_boards,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(url)

        returned_ids = {board["id"] for board in response.data}

        for board in another_user_boards:
            assert board.id not in returned_ids

    def test_returns_empty_list_when_user_has_no_boards(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user=user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == []

    def test_anonymous_user_cannot_list_boards(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestBoardRetrieveView:
    """Tests for BoardViewSet retrieve endpoint."""

    @pytest.fixture
    def board(self, user):
        return BoardFactory(owner=user, name="My Board")

    @pytest.fixture
    def another_board(self, another_user):
        return BoardFactory(owner=another_user, name="Another Board")

    def test_owner_can_retrieve_board(
        self,
        api_client,
        user,
        board,
    ):
        api_client.force_authenticate(user=user)

        url = reverse("board-detail", args=[board.id])

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == board.id
        assert response.data["name"] == board.name
        assert response.data["owner"] == user.id

    def test_retrieve_returns_correct_board(
        self,
        api_client,
        user,
        board,
    ):
        api_client.force_authenticate(user=user)

        url = reverse("board-detail", args=[board.id])

        response = api_client.get(url)

        assert response.data["id"] == board.id
        assert response.data["name"] == board.name
        assert response.data["status"] == board.status
        assert response.data["closed"] == board.closed

    def test_cannot_retrieve_another_users_board(
        self,
        api_client,
        user,
        another_board,
    ):
        api_client.force_authenticate(user=user)

        url = reverse("board-detail", args=[another_board.id])

        response = api_client.get(url)

        # Depending on queryset/permissions this may be 403 or 404.
        assert response.status_code in (403, 404)

    def test_nonexistent_board_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user=user)

        url = reverse("board-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404

    def test_anonymous_user_cannot_retrieve_board(
        self,
        board,
        api_client
    ):
        url = reverse("board-detail", args=[board.id])

        response = api_client.get(url)

        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestBoardCreateView:
    """Tests for BoardViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("board-list")

    @pytest.fixture
    def valid_data(self):
        return {
            "name": "Backend Project",
            "status": "private",
            "background_color": "#00AAFF",
            "closed": False,
        }

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_anonymous_user_cannot_create_board(
        self,
        api_client,
        url,
        valid_data,
    ):
        response = api_client.post(url, valid_data, format="json")

        assert response.status_code == 401

        assert Board.objects.count() == 0

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_create_board(
        self,
        mock_log,
        api_client,
        user,
        url,
        valid_data,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            valid_data,
            format="json",
        )

        assert response.status_code == 201

        board = Board.objects.get(pk=response.data["id"])

        assert board.owner == user
        assert board.name == valid_data["name"]
        assert board.status == valid_data["status"]
        assert board.background_color == valid_data["background_color"]
        assert board.closed is False

        mock_log.assert_called_once()

    @patch("api.board.views.ActivityLog.log")
    def test_owner_is_taken_from_request(
        self,
        mock_log,
        api_client,
        user,
        another_user,
        url,
        valid_data,
    ):
        api_client.force_authenticate(user)

        data = valid_data.copy()
        data["owner"] = another_user.id

        response = api_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == 201

        board = Board.objects.get(pk=response.data["id"])

        assert board.owner == user

        mock_log.assert_called_once()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "payload,error_field",
        [
            (
                {
                    "status": "private",
                },
                "name",
            ),
            (
                {
                    "name": "",
                    "status": "private",
                },
                "name",
            ),
            (
                {
                    "name": "Board",
                    "status": "invalid",
                },
                "status",
            ),
        ],
    )
    def test_invalid_data_returns_400(
        self,
        api_client,
        user,
        url,
        payload,
        error_field,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            payload,
            format="json",
        )

        assert response.status_code == 400
        assert error_field in response.data

        assert Board.objects.count() == 0

    # ------------------------------------------------------------------
    # ActivityLog
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_activity_log_called_with_correct_arguments(
        self,
        mock_log,
        api_client,
        user,
        url,
        valid_data,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            valid_data,
            format="json",
        )

        assert response.status_code == 201

        board = Board.objects.get(pk=response.data["id"])

        mock_log.assert_called_once()

        _, kwargs = mock_log.call_args

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == board
        assert kwargs["board_list"] is None
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "create_board"
        assert kwargs["text"] == f"{board.name} created"



@pytest.mark.django_db
class TestBoardUpdateView:
    """Tests for BoardViewSet.update()."""

    @pytest.fixture
    def board(self, user):
        return BoardFactory(
            owner=user,
            name="Project Alpha",
            status="private",
            background_color="#000000",
            closed=False,
        )

    @pytest.fixture
    def url(self, board):
        return reverse("board-detail", args=[board.pk])

    # ------------------------------------------------------------------
    # Authentication / Permission
    # ------------------------------------------------------------------

    def test_anonymous_user_cannot_update_board(
        self,
        api_client,
        url,
    ):
        response = api_client.patch(
            url,
            {"name": "Updated"},
            format="json",
        )

        assert response.status_code == 401

    def test_non_owner_cannot_update_board(
        self,
        api_client,
        another_user,
        board,
        url,
    ):
        api_client.force_authenticate(another_user)

        response = api_client.patch(
            url,
            {"name": "Updated"},
            format="json",
        )

        # Because get_queryset() filters by owner.
        assert response.status_code == 404

        board.refresh_from_db()
        assert board.name == "Project Alpha"

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_update_name(
        self,
        mock_log,
        api_client,
        user,
        board,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            {"name": "Backend"},
            format="json",
        )

        assert response.status_code == 200

        board.refresh_from_db()

        assert board.name == "Backend"

        mock_log.assert_called_once()

        _, kwargs = mock_log.call_args

        assert kwargs["action_type"] == "edit_board_title"
        assert kwargs["board"] == board
        assert kwargs["text"] == (
            "The name of the board was changed "
            "from Project Alpha to Backend "
        )

    @patch("api.board.views.ActivityLog.log")
    def test_update_status(
        self,
        mock_log,
        api_client,
        user,
        url,
        board,
    ):
        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            {"status": "public"},
            format="json",
        )

        assert response.status_code == 200

        board.refresh_from_db()

        assert board.status == "public"

        _, kwargs = mock_log.call_args

        assert kwargs["action_type"] == "edit_board_status"

    @patch("api.board.views.ActivityLog.log")
    def test_close_board(
        self,
        mock_log,
        api_client,
        user,
        board,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            {"closed": True},
            format="json",
        )

        assert response.status_code == 200

        board.refresh_from_db()

        assert board.closed is True

        _, kwargs = mock_log.call_args

        assert kwargs["action_type"] == "close_board"

    @patch("api.board.views.ActivityLog.log")
    def test_update_background_color(
        self,
        mock_log,
        api_client,
        user,
        board,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            {"background_color": "#FFFFFF"},
            format="json",
        )

        assert response.status_code == 200

        board.refresh_from_db()

        assert board.background_color == "#FFFFFF"

        _, kwargs = mock_log.call_args

        assert kwargs["action_type"] == "edit_background"

    # ------------------------------------------------------------------
    # Multiple changes
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_multiple_changes_create_multiple_activity_logs(
        self,
        mock_log,
        api_client,
        user,
        board,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            {
                "name": "Backend",
                "status": "public",
                "closed": True,
            },
            format="json",
        )

        assert response.status_code == 200

        assert mock_log.call_count == 3

        expected_calls = [
            call(
                request=mock_log.call_args_list[0].kwargs["request"],
                user=user,
                board=board,
                board_list=None,
                card=None,
                action_type="edit_board_title",
                text="The name of the board was changed from Project Alpha to Backend ",
            ),
            call(
                request=mock_log.call_args_list[1].kwargs["request"],
                user=user,
                board=board,
                board_list=None,
                card=None,
                action_type="edit_board_status",
                text="The visibility of the board was changed from private to public ",
            ),
            call(
                request=mock_log.call_args_list[2].kwargs["request"],
                user=user,
                board=board,
                board_list=None,
                card=None,
                action_type="close_board",
                text="The 'Backend board closed",
            ),
        ]

        mock_log.assert_has_calls(expected_calls)

    # ------------------------------------------------------------------
    # No activity
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_no_activity_logged_when_no_tracked_fields_change(
        self,
        mock_log,
        api_client,
        user,
        board,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            {},
            format="json",
        )

        assert response.status_code == 200

        mock_log.assert_not_called()



@pytest.mark.django_db
class TestBoardDestroyView:
    """Tests for BoardViewSet.destroy()."""

    @pytest.fixture
    def board(self, user):
        return BoardFactory(owner=user, name="Project Alpha")

    @pytest.fixture
    def url(self, board):
        return reverse("board-detail", args=[board.pk])

    # --------------------------------------------------------
    # Authentication / Permission
    # --------------------------------------------------------

    def test_anonymous_user_cannot_delete_board(
        self,
        api_client,
        board,
        url,
    ):
        response = api_client.delete(url)

        assert response.status_code == 401

        assert Board.objects.filter(pk=board.pk).exists()

    def test_non_owner_cannot_delete_board(
        self,
        api_client,
        another_user,
        board,
        url,
    ):
        api_client.force_authenticate(another_user)

        response = api_client.delete(url)

        # get_queryset() filters by owner
        assert response.status_code == 404

        assert Board.objects.filter(pk=board.pk).exists()

    # --------------------------------------------------------
    # Delete
    # --------------------------------------------------------

    def test_owner_can_delete_board(
        self,
        api_client,
        user,
        board,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not Board.objects.filter(pk=board.pk).exists()

    def test_delete_nonexistent_board_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("board-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End BoardViewSet Tests
#======================



#======================
#  Start CardViewSet Tests
#======================

@pytest.mark.django_db
class TestCardListView:
    """Tests for CardViewSet list endpoint."""

    @pytest.fixture
    def url(self):
        return reverse("card-list")

    @pytest.fixture
    def owner_cards(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)

        return [
            CardFactory(board_list=board_list, name="Card 1"),
            CardFactory(board_list=board_list, name="Card 2"),
            CardFactory(board_list=board_list, name="Card 3"),
        ]

    @pytest.fixture
    def member_cards(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)

        return [
            CardFactory(board_list=board_list, name="Member Card 1"),
            CardFactory(board_list=board_list, name="Member Card 2"),
        ]

    @pytest.fixture
    def stranger_cards(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)

        return [
            CardFactory(board_list=board_list, name="Hidden Card 1"),
            CardFactory(board_list=board_list, name="Hidden Card 2"),
        ]

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_cards(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_owner_sees_only_own_cards(
        self,
        api_client,
        user,
        url,
        owner_cards,
        stranger_cards,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {card["id"] for card in response.data}
        expected_ids = {card.id for card in owner_cards}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Member
    # ---------------------------------------------------------

    def test_board_member_can_list_cards(
        self,
        api_client,
        user,
        url,
        member_cards,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {card["id"] for card in response.data}
        expected_ids = {card.id for card in member_cards}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Visibility
    # ---------------------------------------------------------

    def test_user_cannot_see_unrelated_cards(
        self,
        api_client,
        user,
        url,
        stranger_cards,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {card["id"] for card in response.data}

        for card in stranger_cards:
            assert card.id not in returned_ids

    def test_returns_empty_list_when_user_has_no_accessible_cards(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == []

    # ---------------------------------------------------------
    # distinct()
    # ---------------------------------------------------------

    def test_duplicate_memberships_do_not_duplicate_cards(
        self,
        api_client,
        user,
        url,
    ):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        with pytest.raises(IntegrityError) as exc_info:

            # second membership shouldn't duplicate results
            BoardMembership.objects.create(
                board=board,
                user=user,
                member_type="admin",
                accepted=True,
            )

        assert "UNIQUE constraint failed" in str(exc_info)





@pytest.mark.django_db
class TestCardRetrieveView:
    """Tests for CardViewSet retrieve endpoint."""

    @pytest.fixture
    def owner_card(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        return CardFactory(
            board_list=board_list,
            name="Owner Card",
        )

    @pytest.fixture
    def member_card(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)

        return CardFactory(
            board_list=board_list,
            name="Member Card",
        )

    @pytest.fixture
    def stranger_card(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)

        return CardFactory(
            board_list=board_list,
            name="Hidden Card",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_card(
        self,
        api_client,
        owner_card,
    ):
        url = reverse("card-detail", args=[owner_card.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_owner_can_retrieve_card(
        self,
        api_client,
        user,
        owner_card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[owner_card.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_card.id
        assert response.data["name"] == owner_card.name
        assert response.data["board_list"] == owner_card.board_list.id

    # ---------------------------------------------------------
    # Member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_card(
        self,
        api_client,
        user,
        member_card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[member_card.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_card.id
        assert response.data["name"] == member_card.name

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_unrelated_card(
        self,
        api_client,
        user,
        stranger_card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[stranger_card.pk])

        response = api_client.get(url)

        # get_queryset() filters accessible cards
        assert response.status_code == 404

    def test_nonexistent_card_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404



@pytest.mark.django_db
class TestCardCreateView:
    """Tests for CardViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("card-list")

    @pytest.fixture
    def valid_data(self, board_list):
        return {
            "board_list": board_list.id,
            "name": "Implement authentication",
            "description": "Create login and registration",
            "completed": False,
        }

    @pytest.fixture
    def stranger_board_list(self, another_user):
        board = BoardFactory(owner=another_user)
        board_list = BoardListFactory(board=board, name="strange_board_list")
        return board_list

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_anonymous_user_cannot_create_card(
        self,
        api_client,
        url,
        valid_data,
    ):
        response = api_client.post(url, valid_data, format="json")

        assert response.status_code == 401
        assert Card.objects.count() == 0

    # ------------------------------------------------------------------
    # Permission
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_create_card(
        self,
        mock_log,
        api_client,
        user,
        board_list,
        url,
        valid_data,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(url, valid_data, format="json")

        assert response.status_code == 201

        card = Card.objects.get(pk=response.data["id"])

        assert card.board_list == board_list
        assert card.name == valid_data["name"]
        assert card.description == valid_data["description"]
        assert card.completed is False

        mock_log.assert_called_once()

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_card(
        self,
        mock_log,
        api_client,
        another_user,
        board,
        url,
    ):
        BoardMembership.objects.create(
            board=board,
            user=another_user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)

        api_client.force_authenticate(another_user)

        payload = {
            "board_list": board_list.id,
            "name": "Member Card",
        }

        response = api_client.post(url, payload, format="json")

        assert response.status_code == 201

        card = Card.objects.get(pk=response.data["id"])

        assert card.name == payload["name"]
        assert card.board_list == board_list

        mock_log.assert_called_once()

    def test_user_cannot_create_card_on_unrelated_board(
        self,
        api_client,
        user,
        stranger_board_list,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "board_list": stranger_board_list.id,
                "name": "Hack",
            },
            format="json",
        )

        assert response.status_code == 403
        assert Card.objects.count() == 0

    def test_nonexistent_board_list_returns_403(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "board_list": 999999,
                "name": "Card",
            },
            format="json",
        )

        assert response.status_code == 403
        assert Card.objects.count() == 0

    def test_missing_board_list_returns_403(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Card",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "board_list" in response.data

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_invalid_data_returns_400(
        self,
        api_client,
        user,
        board_list,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "board_list": board_list.id,
                "name": "",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "name" in response.data

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_activity_log_called_with_correct_arguments(
        self,
        mock_log,
        api_client,
        user,
        board_list,
        url,
        valid_data,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(url, valid_data, format="json")

        assert response.status_code == 201

        card = Card.objects.get(pk=response.data["id"])

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == board_list.board
        assert kwargs["board_list"] == board_list
        assert kwargs["card"] == card
        assert kwargs["action_type"] == "create_card"
        assert kwargs["text"] == (
            f"The '{card.name}' card in the {board_list.name} list was created"
        )



@pytest.mark.django_db
class TestCardUpdateView:
    """Tests for CardViewSet.update()."""

    @pytest.fixture
    def card(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)

        return CardFactory(
            board_list=board_list,
            name="Old Card",
            description="Old description",
            completed=False,
        )

    @pytest.fixture
    def member_card(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)

        return CardFactory(
            board_list=board_list,
            name="Member Card",
        )

    @pytest.fixture
    def stranger_card(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)

        return CardFactory(
            board_list=board_list,
            name="Private Card",
        )

    @pytest.fixture
    def url(self, card):
        return reverse("card-detail", args=[card.pk])

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    def test_anonymous_user_cannot_update_card(
        self,
        api_client,
        url,
    ):
        response = api_client.patch(
            url,
            {"name": "Updated"},
            format="json",
        )

        assert response.status_code == 401

    # --------------------------------------------------------
    # Permission
    # --------------------------------------------------------

    def test_owner_can_update_card(
        self,
        api_client,
        user,
        card,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.patch(
            url,
            {
                "name": "Updated Card",
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert card.name == "Updated Card"

    def test_board_member_can_update_card(
        self,
        api_client,
        user,
        member_card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[member_card.pk])

        response = api_client.patch(
            url,
            {
                "name": "Updated Member Card",
            },
            format="json",
        )

        assert response.status_code == 200

        member_card.refresh_from_db()

        assert member_card.name == "Updated Member Card"

    def test_user_cannot_update_unrelated_card(
        self,
        api_client,
        user,
        stranger_card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[stranger_card.pk])

        response = api_client.patch(
            url,
            {
                "name": "Hack",
            },
            format="json",
        )

        # get_queryset() hides inaccessible objects
        assert response.status_code == 404

    def test_update_nonexistent_card_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[999999])

        response = api_client.patch(
            url,
            {
                "name": "Updated",
            },
            format="json",
        )

        assert response.status_code == 404

    @patch("api.board.views.ActivityLog.log")
    def test_update_name_logs_activity(
        self,
        mock_log,
        api_client,
        user,
        card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        old_name = card.name

        response = api_client.patch(
            url,
            {
                "name": "New Card",
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert card.name == "New Card"

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == card.board_list.board
        assert kwargs["board_list"] == card.board_list
        assert kwargs["card"] == card
        assert kwargs["action_type"] == "edit_card_title"
        assert kwargs["text"] == (
            f"The name of the card was was changed from {old_name} to New Card "
        )


    @patch("api.board.views.ActivityLog.log")
    def test_update_description_logs_activity(
        self,
        mock_log,
        api_client,
        user,
        card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {
                "description": "Updated description",
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert card.description == "Updated description"

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "edit_card_description"
        assert kwargs["text"] == (
            f"The description of {card.name} card was changed"
        )


    @patch("api.board.views.ActivityLog.log")
    def test_update_start_date_logs_activity(
        self,
        mock_log,
        api_client,
        user,
        card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {
                "start_date": "2026-07-15",
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert str(card.start_date) == "2026-07-15"

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "edit_start_date"


    @patch("api.board.views.ActivityLog.log")
    def test_update_due_date_logs_activity(
    self,
    mock_log,
    api_client,
    user,
    card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {
                "due_date": "2026-07-20T14:30",
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert card.due_date is not None

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "edit_due_date"


    @patch("api.board.views.ActivityLog.log")
    def test_update_completed_logs_activity(
        self,
        mock_log,
        api_client,
        user,
        card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {
                "completed": True,
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert card.completed is True

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "edit_card_completed"
        assert kwargs["text"] == (
            f"The completeness of the '{card.name}' card is changed to 'True'"
        )

    @patch("api.board.views.ActivityLog.log")
    def test_move_card_logs_activity(
        self,
        mock_log,
        api_client,
        user,
        card,
    ):
        api_client.force_authenticate(user)

        old_list = card.board_list
        new_list = BoardListFactory(
            board=old_list.board,
            name="Done",
        )

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {
                "board_list": new_list.id,
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert card.board_list == new_list

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "move_card"

        assert kwargs["text"] == (
            f"'{card.name}' card moved from "
            f"'{old_list.name}' list to '{new_list.name}' list"
        )

    @patch("api.board.views.ActivityLog.log")
    def test_set_cover_color_logs_activity(
        self,
        mock_log,
        api_client,
        user,
        card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {
                "cover_color": "#ff0000",
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert card.cover_color == "#ff0000"

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "set_card_cover"

    @patch("api.board.views.ActivityLog.log")
    def test_remove_cover_logs_activity(
        self,
        mock_log,
        api_client,
        user,
    ):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)

        card = CardFactory(
            board_list=board_list,
            cover_color="#00ff00",
        )

        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {
                "cover_color": "",
            },
            format="json",
        )

        assert response.status_code == 200

        card.refresh_from_db()

        assert card.cover_color == ""

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "set_card_cover"

    @patch("api.board.views.ActivityLog.log")
    def test_multiple_changes_log_multiple_activities(
        self,
        mock_log,
        api_client,
        user,
        card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {
                "name": "Backend",
                "description": "Updated",
                "completed": True,
            },
            format="json",
        )

        assert response.status_code == 200

        assert mock_log.call_count == 3

        action_types = [
            call.kwargs["action_type"]
            for call in mock_log.call_args_list
        ]

        assert action_types == [
            "edit_card_title",
            "edit_card_description",
            "edit_card_completed",
        ]

    @patch("api.board.views.ActivityLog.log")
    def test_no_activity_logged_when_no_tracked_fields_change(
        self,
        mock_log,
        api_client,
        user,
        card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[card.pk])

        response = api_client.patch(
            url,
            {},
            format="json",
        )

        assert response.status_code == 200

        mock_log.assert_not_called()



@pytest.mark.django_db
class TestCardDestroyView:
    """Tests for CardViewSet.destroy()."""



    @pytest.fixture
    def owner_card(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)

        return CardFactory(
            board_list=board_list,
            name="Owner Card",
        )

    @pytest.fixture
    def member_card(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)

        return CardFactory(
            board_list=board_list,
            name="Member Card",
        )

    @pytest.fixture
    def stranger_card(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)

        return CardFactory(
            board_list=board_list,
            name="Private Card",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_card(
        self,
        api_client,
        owner_card,
    ):
        url = reverse("card-list", args=[owner_card.pk])

        response = api_client.delete(url)

        assert response.status_code == 404



    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_owner_can_delete_card(
        self,
        api_client,
        user,
        owner_card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[owner_card.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not Card.objects.filter(pk=owner_card.pk).exists()

    def test_board_member_can_delete_card(
        self,
        api_client,
        user,
        member_card,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[member_card.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not Card.objects.filter(pk=member_card.pk).exists()

    def test_user_cannot_delete_unrelated_card(
        self,
        api_client,
        user,
        stranger_card,
    ):
        api_client.force_authenticate(user)
        url = reverse("card-detail", args=[stranger_card.pk])


        response = api_client.delete(url)

        # Hidden by get_queryset()
        assert response.status_code == 404

        assert Card.objects.filter(pk=stranger_card.pk).exists()

    # ---------------------------------------------------------
    # Not Found
    # ---------------------------------------------------------

    def test_delete_nonexistent_card_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("card-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404

#======================
#  End CardViewSet Tests
#======================



#======================
#  Start ChecklistViewSet Tests
#======================



@pytest.mark.django_db
class TestChecklistListView:
    """Tests for ChecklistViewSet.list()."""

    @pytest.fixture
    def url(self):
        return reverse("checklist-list")

    @pytest.fixture
    def owner_checklists(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory.create_batch(
            3,
            card=card,
        )

    @pytest.fixture
    def member_checklists(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory.create_batch(
            2,
            card=card,
        )

    @pytest.fixture
    def stranger_checklists(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory.create_batch(
            4,
            card=card,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_checklists(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_owner_sees_only_own_checklists(
        self,
        api_client,
        user,
        url,
        owner_checklists,
        stranger_checklists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {
            item["id"]
            for item in response.data
        }

        expected_ids = {
            checklist.id
            for checklist in owner_checklists
        }

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_sees_board_checklists(
        self,
        api_client,
        user,
        url,
        member_checklists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {
            item["id"]
            for item in response.data
        }

        expected_ids = {
            checklist.id
            for checklist in member_checklists
        }

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Filtering
    # ---------------------------------------------------------

    def test_list_excludes_other_users_checklists(
        self,
        api_client,
        user,
        url,
        owner_checklists,
        stranger_checklists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {
            item["id"]
            for item in response.data
        }

        stranger_ids = {
            checklist.id
            for checklist in stranger_checklists
        }

        assert returned_ids.isdisjoint(stranger_ids)

    # ---------------------------------------------------------
    # Distinct
    # ---------------------------------------------------------

    def test_list_contains_no_duplicates(
        self,
        api_client,
        user,
        url,
        owner_checklists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        ids = [
            item["id"]
            for item in response.data
        ]

        assert len(ids) == len(set(ids))

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        url,
        owner_checklists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        item = response.data[0]

        assert set(item.keys()) == {
            "id",
            "name",
            "checklist_items",
            "card",
        }



@pytest.mark.django_db
class TestChecklistRetrieveView:
    """Tests for ChecklistViewSet.retrieve()."""

    @pytest.fixture
    def owner_checklist(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory(
            card=card,
            name="Backend Tasks",
        )

    @pytest.fixture
    def member_checklist(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory(
            card=card,
            name="Frontend Tasks",
        )

    @pytest.fixture
    def stranger_checklist(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory(
            card=card,
            name="Private Checklist",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_checklist(
        self,
        api_client,
        owner_checklist,
    ):
        url = reverse("checklist-detail", args=[owner_checklist.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_owner_can_retrieve_checklist(
        self,
        api_client,
        user,
        owner_checklist,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[owner_checklist.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_checklist.id
        assert response.data["name"] == owner_checklist.name
        assert response.data["card"] == owner_checklist.card.id

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_checklist(
        self,
        api_client,
        user,
        member_checklist,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[member_checklist.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_checklist.id
        assert response.data["name"] == member_checklist.name

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_unrelated_checklist(
        self,
        api_client,
        user,
        stranger_checklist,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[stranger_checklist.pk])

        response = api_client.get(url)

        # Hidden by get_queryset()
        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_retrieve_nonexistent_checklist_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        owner_checklist,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[owner_checklist.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data.keys()) == {
            "id",
            "name",
            "checklist_items",
            "card",
        }

        assert isinstance(response.data["checklist_items"], list)




@pytest.mark.django_db
class TestChecklistCreateView:
    """Tests for ChecklistViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("checklist-list")

    @pytest.fixture
    def owner_card(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        return CardFactory(board_list=board_list)

    @pytest.fixture
    def member_card(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)

        return CardFactory(board_list=board_list)

    @pytest.fixture
    def stranger_card(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)

        return CardFactory(board_list=board_list)

    @pytest.fixture
    def valid_data(self, owner_card):
        return {
            "name": "Backend Checklist",
            "card": owner_card.id,
        }

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_checklist(
        self,
        api_client,
        url,
        valid_data,
    ):
        response = api_client.post(
            url,
            valid_data,
            format="json",
        )

        assert response.status_code == 401

        assert CheckList.objects.count() == 0

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_create_checklist(
        self,
        mock_log,
        api_client,
        user,
        url,
        valid_data,
        owner_card,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            valid_data,
            format="json",
        )

        assert response.status_code == 201

        checklist = CheckList.objects.get()

        assert checklist.name == valid_data["name"]
        assert checklist.card == owner_card

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_card.board_list.board
        assert kwargs["board_list"] == owner_card.board_list
        assert kwargs["card"] == owner_card
        assert kwargs["action_type"] == "add_checklist"
        assert kwargs["text"] == (
            f"'{checklist.name}' checklist added"
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_checklist(
        self,
        mock_log,
        api_client,
        user,
        url,
        member_card,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Frontend Checklist",
                "card": member_card.id,
            },
            format="json",
        )

        assert response.status_code == 201

        checklist = CheckList.objects.get()

        assert checklist.card == member_card

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_create_checklist_for_unrelated_card(
        self,
        api_client,
        user,
        url,
        stranger_card,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Hack",
                "card": stranger_card.id,
            },
            format="json",
        )

        assert response.status_code == 403

        assert CheckList.objects.count() == 0

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_name_is_required(
        self,
        api_client,
        user,
        url,
        owner_card,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": owner_card.id,
            },
            format="json",
        )

        assert response.status_code == 400

        assert "name" in response.data

    def test_card_is_required(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Checklist",
            },
            format="json",
        )


        assert response.status_code == 400

    def test_invalid_card_returns_403(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Checklist",
                "card": 999999,
            },
            format="json",
        )

        assert response.status_code == 403



@pytest.mark.django_db
class TestChecklistDestroyView:
    """Tests for ChecklistViewSet.destroy()."""

    @pytest.fixture
    def owner_checklist(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory(
            card=card,
            name="Backend Checklist",
        )

    @pytest.fixture
    def member_checklist(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory(
            card=card,
            name="Frontend Checklist",
        )

    @pytest.fixture
    def stranger_checklist(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory(
            card=card,
            name="Private Checklist",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_checklist(
        self,
        api_client,
        owner_checklist,
    ):
        url = reverse("checklist-detail", args=[owner_checklist.pk])

        response = api_client.delete(url)

        assert response.status_code == 401

        assert CheckList.objects.filter(pk=owner_checklist.pk).exists()

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_delete_checklist(
        self,
        mock_log,
        api_client,
        user,
        owner_checklist,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[owner_checklist.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not CheckList.objects.filter(
            pk=owner_checklist.pk
        ).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_checklist.card.board_list.board
        assert kwargs["board_list"] == owner_checklist.card.board_list
        assert kwargs["card"] == owner_checklist.card
        assert kwargs["action_type"] == "remove_checklist"
        assert kwargs["text"] == (
            f"The '{owner_checklist.name}' checklist in "
            f"'{owner_checklist.card.name}' card was removed"
        )

    # ---------------------------------------------------------
    # Member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_delete_checklist(
        self,
        mock_log,
        api_client,
        user,
        member_checklist,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[member_checklist.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not CheckList.objects.filter(
            pk=member_checklist.pk
        ).exists()

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_delete_unrelated_checklist(
        self,
        api_client,
        user,
        stranger_checklist,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[stranger_checklist.pk])

        response = api_client.delete(url)

        # Hidden by get_queryset()
        assert response.status_code == 404

        assert CheckList.objects.filter(
            pk=stranger_checklist.pk
        ).exists()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_checklist_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklist-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End ChecklistViewSet Tests
#======================