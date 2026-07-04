import io
from PIL import Image
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from django.urls import reverse
from unittest.mock import call, patch
from rest_framework import status
from .conftest import (
    BoardFactory, 
    UserFactory, 
    BoardListFactory, 
    CardFactory, 
    CheckListFactory, 
    CheckListItemFactory,
    CommentFactory,
    CardFileFactory,
    CardImageFactory,
    LinkAttachmentFactory,
    CardLabelFactory,
    CardMembershipFactory
    )
from board.models import (
    Board, 
    BoardMembership, 
    Card, 
    CheckList, 
    ChecklistItem, 
    Comment,
    CardFile,
    CardImage,
    LinkAttachment,
    CardLabel,
    BoardList,
    CardMembership
    )


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


#======================
#  Start ChecklistItemViewSet Tests
#======================


@pytest.mark.django_db
class TestChecklistItemListView:
    """Tests for ChecklistItemViewSet.list()."""

    @pytest.fixture
    def url(self):
        return reverse("checklistitem-list")

    @pytest.fixture
    def owner_items(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory.create_batch(
            3,
            checklist=checklist,
        )

    @pytest.fixture
    def member_items(self, user):
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
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory.create_batch(
            2,
            checklist=checklist,
        )

    @pytest.fixture
    def stranger_items(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory.create_batch(
            4,
            checklist=checklist,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_items(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_owner_sees_only_own_items(
        self,
        api_client,
        user,
        url,
        owner_items,
        stranger_items,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {
            item["id"]
            for item in response.data
        }

        expected_ids = {
            item.id
            for item in owner_items
        }

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Member
    # ---------------------------------------------------------

    def test_board_member_sees_board_items(
        self,
        api_client,
        user,
        url,
        member_items,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {
            item["id"]
            for item in response.data
        }

        expected_ids = {
            item.id
            for item in member_items
        }

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Filtering
    # ---------------------------------------------------------

    def test_list_excludes_other_users_items(
        self,
        api_client,
        user,
        url,
        owner_items,
        stranger_items,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {
            item["id"]
            for item in response.data
        }

        stranger_ids = {
            item.id
            for item in stranger_items
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
        owner_items,
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
        owner_items,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        item = response.data[0]

        assert set(item.keys()) == {
            "id",
            "name",
            "is_completed",
            "checklist",
        }


@pytest.mark.django_db
class TestChecklistItemRetrieveView:
    """Tests for ChecklistItemViewSet.retrieve()."""

    @pytest.fixture
    def owner_item(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
            name="Write tests",
            is_completed=False,
        )

    @pytest.fixture
    def member_item(self, user):
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
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
            name="Review PR",
        )

    @pytest.fixture
    def stranger_item(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
            name="Private Item",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_item(
        self,
        api_client,
        owner_item,
    ):
        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_owner_can_retrieve_item(
        self,
        api_client,
        user,
        owner_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_item.id
        assert response.data["name"] == owner_item.name
        assert response.data["is_completed"] == owner_item.is_completed
        assert response.data["checklist"] == owner_item.checklist.id

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_item(
        self,
        api_client,
        user,
        member_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[member_item.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_item.id
        assert response.data["name"] == member_item.name

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_unrelated_item(
        self,
        api_client,
        user,
        stranger_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[stranger_item.pk])

        response = api_client.get(url)

        # Hidden by get_queryset()
        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_retrieve_nonexistent_item_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        owner_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data.keys()) == {
            "id",
            "name",
            "is_completed",
            "checklist",
        }


@pytest.mark.django_db
class TestChecklistItemCreateView:
    """Tests for ChecklistItemViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("checklistitem-list")

    @pytest.fixture
    def owner_checklist(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory(
            card=card,
            name="Backend",
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

        return CheckListFactory(card=card)

    @pytest.fixture
    def stranger_checklist(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CheckListFactory(card=card)

    @pytest.fixture
    def valid_data(self, owner_checklist):
        return {
            "name": "Write serializer tests",
            "checklist": owner_checklist.id,
        }

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_item(
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

        assert ChecklistItem.objects.count() == 0

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_create_item(
        self,
        mock_log,
        api_client,
        user,
        url,
        valid_data,
        owner_checklist,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            valid_data,
            format="json",
        )

        assert response.status_code == 201

        item = ChecklistItem.objects.get()

        assert item.name == valid_data["name"]
        assert item.checklist == owner_checklist
        assert item.is_completed is False

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_checklist.card.board_list.board
        assert kwargs["board_list"] == owner_checklist.card.board_list
        assert kwargs["card"] == owner_checklist.card
        assert kwargs["action_type"] == "add_checklist_item"
        assert kwargs["text"] == (
            f"'{item.name}' item added to "
            f"'{owner_checklist.name}' in "
            f"'{owner_checklist.card.name}' card"
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_item(
        self,
        mock_log,
        api_client,
        user,
        url,
        member_checklist,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Review code",
                "checklist": member_checklist.id,
            },
            format="json",
        )

        assert response.status_code == 201

        item = ChecklistItem.objects.get()

        assert item.checklist == member_checklist

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_create_item_for_unrelated_checklist(
        self,
        api_client,
        user,
        url,
        stranger_checklist,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Hack",
                "checklist": stranger_checklist.id,
            },
            format="json",
        )

        assert response.status_code == 403

        assert ChecklistItem.objects.count() == 0

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_name_is_required(
        self,
        api_client,
        user,
        url,
        owner_checklist,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "checklist": owner_checklist.id,
            },
            format="json",
        )

        assert response.status_code == 400

        assert "name" in response.data

    def test_checklist_is_required(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Write tests",
            },
            format="json",
        )


        assert response.status_code == 400

    def test_invalid_checklist_returns_403(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Write tests",
                "checklist": 999999,
            },
            format="json",
        )

        assert response.status_code == 403


@pytest.mark.django_db
class TestChecklistItemUpdateView:
    """Tests for ChecklistItemViewSet.update()."""

    @pytest.fixture
    def owner_item(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
            name="Old Item",
            is_completed=False,
        )

    @pytest.fixture
    def member_item(self, user):
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
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
            name="Member Item",
            is_completed=False,
        )

    @pytest.fixture
    def stranger_item(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_item(
        self,
        api_client,
        owner_item,
    ):
        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.patch(
            url,
            {"name": "New Name"},
            format="json",
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Name update
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_update_name(
        self,
        mock_log,
        api_client,
        user,
        owner_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.patch(
            url,
            {"name": "New Item"},
            format="json",
        )

        assert response.status_code == 200

        owner_item.refresh_from_db()

        assert owner_item.name == "New Item"

        mock_log.assert_called_once_with(
            request=mock_log.call_args.kwargs["request"],
            user=user,
            board=owner_item.checklist.card.board_list.board,
            board_list=owner_item.checklist.card.board_list,
            card=owner_item.checklist.card,
            action_type="edit_checklist_item_name",
            text="The name of the item was changed from 'Old Item' to 'New Item' ",
        )

    # ---------------------------------------------------------
    # Completion update
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_update_completion(
        self,
        mock_log,
        api_client,
        user,
        owner_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.patch(
            url,
            {"is_completed": True},
            format="json",
        )

        assert response.status_code == 200

        owner_item.refresh_from_db()

        assert owner_item.is_completed is True

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["action_type"] == "edit_checklist_item_completed"

    # ---------------------------------------------------------
    # Multiple changes
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_updating_name_and_completion_logs_two_activities(
        self,
        mock_log,
        api_client,
        user,
        owner_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.patch(
            url,
            {
                "name": "Updated",
                "is_completed": True,
            },
            format="json",
        )

        assert response.status_code == 200

        owner_item.refresh_from_db()

        assert owner_item.name == "Updated"
        assert owner_item.is_completed is True

        assert mock_log.call_count == 2

        action_types = [
            c.kwargs["action_type"]
            for c in mock_log.call_args_list
        ]

        assert "edit_checklist_item_name" in action_types
        assert "edit_checklist_item_completed" in action_types

    # ---------------------------------------------------------
    # No changes
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_no_activity_when_nothing_changes(
        self,
        mock_log,
        api_client,
        user,
        owner_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.patch(
            url,
            {
                "name": owner_item.name,
                "is_completed": owner_item.is_completed,
            },
            format="json",
        )

        assert response.status_code == 200

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Member
    # ---------------------------------------------------------

    def test_board_member_can_update_item(
        self,
        api_client,
        user,
        member_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[member_item.pk])

        response = api_client.patch(
            url,
            {"name": "Updated"},
            format="json",
        )

        assert response.status_code == 200

        member_item.refresh_from_db()

        assert member_item.name == "Updated"

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_update_unrelated_item(
        self,
        api_client,
        user,
        stranger_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[stranger_item.pk])

        response = api_client.patch(
            url,
            {"name": "Hack"},
            format="json",
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_update_nonexistent_item_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[999999])

        response = api_client.patch(
            url,
            {"name": "Updated"},
            format="json",
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_empty_name_returns_400(
        self,
        api_client,
        user,
        owner_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.patch(
            url,
            {"name": ""},
            format="json",
        )

        assert response.status_code == 400

        assert "name" in response.data



@pytest.mark.django_db
class TestChecklistItemDestroyView:
    """Tests for ChecklistItemViewSet.destroy()."""

    @pytest.fixture
    def owner_item(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
            name="Write tests",
        )

    @pytest.fixture
    def member_item(self, user):
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
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
            name="Review code",
        )

    @pytest.fixture
    def stranger_item(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)
        checklist = CheckListFactory(card=card)

        return CheckListItemFactory(
            checklist=checklist,
            name="Private item",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_item(
        self,
        api_client,
        owner_item,
    ):
        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.delete(url)

        assert response.status_code == 401

        assert ChecklistItem.objects.filter(pk=owner_item.pk).exists()

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_owner_can_delete_item(
        self,
        mock_log,
        api_client,
        user,
        owner_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[owner_item.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not ChecklistItem.objects.filter(
            pk=owner_item.pk
        ).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_item.checklist.card.board_list.board
        assert kwargs["board_list"] == owner_item.checklist.card.board_list
        assert kwargs["card"] == owner_item.checklist.card
        assert kwargs["action_type"] == "remove_checklist_item"
        assert kwargs["text"] == (
            f"The '{owner_item.name}' item in "
            f"'{owner_item.checklist.name}' checklist was removed"
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_delete_item(
        self,
        mock_log,
        api_client,
        user,
        member_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[member_item.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not ChecklistItem.objects.filter(
            pk=member_item.pk
        ).exists()

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_delete_unrelated_item(
        self,
        api_client,
        user,
        stranger_item,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[stranger_item.pk])

        response = api_client.delete(url)

        # Hidden by get_queryset()
        assert response.status_code == 404

        assert ChecklistItem.objects.filter(
            pk=stranger_item.pk
        ).exists()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_item_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("checklistitem-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End ChecklistItemViewSet Tests
#======================

#======================
#  Start CommentViewSet Tests
#======================


@pytest.mark.django_db
class TestCommentListView:
    """Tests for CommentViewSet.list()."""

    @pytest.fixture
    def url(self):
        return reverse("comment-list")

    @pytest.fixture
    def owner_comments(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CommentFactory.create_batch(
            3,
            card=card,
            user=user,
        )

    @pytest.fixture
    def member_comments(self, user):
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

        return CommentFactory.create_batch(
            2,
            card=card,
            user=owner,
        )

    @pytest.fixture
    def stranger_comments(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CommentFactory.create_batch(
            4,
            card=card,
            user=owner,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_comments(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_owner_can_list_board_comments(
        self,
        api_client,
        user,
        url,
        owner_comments,
        stranger_comments,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {comment.id for comment in owner_comments}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Member
    # ---------------------------------------------------------

    def test_board_member_can_list_comments(
        self,
        api_client,
        user,
        url,
        member_comments,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {comment.id for comment in member_comments}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Filtering
    # ---------------------------------------------------------

    def test_comments_from_other_boards_are_not_returned(
        self,
        api_client,
        user,
        url,
        owner_comments,
        stranger_comments,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {item["id"] for item in response.data}
        stranger_ids = {comment.id for comment in stranger_comments}

        assert returned_ids.isdisjoint(stranger_ids)

    # ---------------------------------------------------------
    # Distinct
    # ---------------------------------------------------------

    def test_list_contains_no_duplicate_comments(
        self,
        api_client,
        user,
        url,
        owner_comments,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        ids = [item["id"] for item in response.data]

        assert len(ids) == len(set(ids))

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        url,
        owner_comments,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data[0].keys()) == {
            "id",
            "user",
            "content",
            "timestamp",
            "edited",
            "card",
            "reply",
        }



@pytest.mark.django_db
class TestCommentRetrieveView:
    """Tests for CommentViewSet.retrieve()."""

    @pytest.fixture
    def owner_comment(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CommentFactory(
            user=user,
            card=card,
            content="Owner comment",
            edited=False,
        )

    @pytest.fixture
    def member_comment(self, user):
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

        return CommentFactory(
            user=owner,
            card=card,
            content="Member visible comment",
        )

    @pytest.fixture
    def stranger_comment(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CommentFactory(
            user=owner,
            card=card,
            content="Private comment",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_comment(
        self,
        api_client,
        owner_comment,
    ):
        url = reverse("comment-detail", args=[owner_comment.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_owner_can_retrieve_comment(
        self,
        api_client,
        user,
        owner_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[owner_comment.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_comment.id
        assert response.data["content"] == owner_comment.content
        assert response.data["edited"] == owner_comment.edited
        assert response.data["card"] == owner_comment.card.id
        assert response.data["user"] == owner_comment.user.id

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_comment(
        self,
        api_client,
        user,
        member_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[member_comment.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_comment.id
        assert response.data["content"] == member_comment.content

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_unrelated_comment(
        self,
        api_client,
        user,
        stranger_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[stranger_comment.pk])

        response = api_client.get(url)

        # Hidden by get_queryset()
        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_retrieve_nonexistent_comment_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        owner_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[owner_comment.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data.keys()) == {
            "id",
            "user",
            "content",
            "timestamp",
            "edited",
            "card",
            "reply",
        }



@pytest.mark.django_db
class TestCommentCreateView:
    """Tests for CommentViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("comment-list")

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
            "card": owner_card.id,
            "content": "This is a new comment.",
        }

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_comment(
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
        assert Comment.objects.count() == 0

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_create_comment(
        self,
        mock_log,
        api_client,
        user,
        url,
        owner_card,
        valid_data,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            valid_data,
            format="json",
        )

        assert response.status_code == 201

        comment = Comment.objects.get()

        assert comment.user == user
        assert comment.card == owner_card
        assert comment.content == valid_data["content"]

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_card.board_list.board
        assert kwargs["board_list"] == owner_card.board_list
        assert kwargs["card"] == owner_card
        assert kwargs["action_type"] == "add_comment"
        assert kwargs["text"] == (
            f"'{user.username}' adds Comment to the '{owner_card.name}' card"
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_comment(
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
                "card": member_card.id,
                "content": "Member comment",
            },
            format="json",
        )

        assert response.status_code == 201

        comment = Comment.objects.get()

        assert comment.user == user
        assert comment.card == member_card
        assert comment.content == "Member comment"

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_create_comment_for_unrelated_card(
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
                "card": stranger_card.id,
                "content": "Unauthorized",
            },
            format="json",
        )

        assert response.status_code == 403
        assert Comment.objects.count() == 0

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
                "content": "Hello",
            },
            format="json",
        )

        # Permission class rejects request before serializer validation.
        assert response.status_code == 403

        assert Comment.objects.count() == 0

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
                "card": 999999,
                "content": "Hello",
            },
            format="json",
        )

        assert response.status_code == 403

        assert Comment.objects.count() == 0

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_content_is_required(
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
        assert "content" in response.data

        assert Comment.objects.count() == 0



@pytest.mark.django_db
class TestCommentUpdateView:
    """Tests for CommentViewSet.update()."""

    @pytest.fixture
    def own_comment(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CommentFactory(
            user=user,
            card=card,
            content="Original comment",
        )

    @pytest.fixture
    def owner_not_comment_owner(self):
        """
        Board owner, but the comment belongs to another user.
        """
        owner = UserFactory()
        comment_author = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=comment_author,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        comment = CommentFactory(
            user=comment_author,
            card=card,
            content="Member comment",
        )

        return owner, comment_author, comment

    @pytest.fixture
    def member_not_comment_owner(self):
        """
        Logged-in member is not the author of the comment.
        """
        owner = UserFactory()
        member = UserFactory()
        comment_author = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=member,
            member_type="member",
            accepted=True,
        )

        BoardMembership.objects.create(
            board=board,
            user=comment_author,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        comment = CommentFactory(
            user=comment_author,
            card=card,
            content="Original",
        )

        return member, comment

    @pytest.fixture
    def stranger_comment(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CommentFactory(
            user=owner,
            card=card,
            content="Private comment",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_comment(
        self,
        api_client,
        own_comment,
    ):
        url = reverse("comment-detail", args=[own_comment.pk])

        response = api_client.patch(
            url,
            {"content": "Updated"},
            format="json",
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner of comment
    # ---------------------------------------------------------

    def test_comment_owner_can_update_comment(
        self,
        api_client,
        user,
        own_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[own_comment.pk])

        response = api_client.patch(
            url,
            {
                "content": "Updated comment",
            },
            format="json",
        )

        assert response.status_code == 200

        own_comment.refresh_from_db()

        assert own_comment.content == "Updated comment"

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_cannot_update_other_users_comment(
        self,
        api_client,
        owner_not_comment_owner,
    ):
        board_owner, _, comment = owner_not_comment_owner

        api_client.force_authenticate(board_owner)

        url = reverse("comment-detail", args=[comment.pk])

        response = api_client.patch(
            url,
            {
                "content": "Updated",
            },
            format="json",
        )

        assert response.status_code == 403

        comment.refresh_from_db()

        assert comment.content == "Member comment"

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_cannot_update_other_users_comment(
        self,
        api_client,
        member_not_comment_owner,
    ):
        member, comment = member_not_comment_owner

        api_client.force_authenticate(member)

        url = reverse("comment-detail", args=[comment.pk])

        response = api_client.patch(
            url,
            {
                "content": "Updated",
            },
            format="json",
        )

        assert response.status_code == 403

        comment.refresh_from_db()

        assert comment.content == "Original"

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_update_comment_outside_his_boards(
        self,
        api_client,
        user,
        stranger_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[stranger_comment.pk])

        response = api_client.patch(
            url,
            {
                "content": "Hack",
            },
            format="json",
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_update_nonexistent_comment_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[999999])

        response = api_client.patch(
            url,
            {
                "content": "Updated",
            },
            format="json",
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_empty_content_returns_400(
        self,
        api_client,
        user,
        own_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[own_comment.pk])

        response = api_client.patch(
            url,
            {
                "content": "",
            },
            format="json",
        )

        assert response.status_code == 400

        assert "content" in response.data



@pytest.mark.django_db
class TestCommentDestroyView:
    """Tests for CommentViewSet.destroy()."""

    @pytest.fixture
    def own_comment(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CommentFactory(
            user=user,
            card=card,
            content="My comment",
        )

    @pytest.fixture
    def owner_not_comment_owner(self):
        """
        Board owner attempts to delete another user's comment.
        """
        board_owner = UserFactory()
        comment_author = UserFactory()

        board = BoardFactory(owner=board_owner)

        BoardMembership.objects.create(
            board=board,
            user=comment_author,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        comment = CommentFactory(
            user=comment_author,
            card=card,
            content="Member comment",
        )

        return board_owner, comment

    @pytest.fixture
    def member_not_comment_owner(self):
        """
        Board member attempts to delete another member's comment.
        """
        owner = UserFactory()
        member = UserFactory()
        author = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=member,
            member_type="member",
            accepted=True,
        )

        BoardMembership.objects.create(
            board=board,
            user=author,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        comment = CommentFactory(
            user=author,
            card=card,
            content="Original comment",
        )

        return member, comment

    @pytest.fixture
    def stranger_comment(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CommentFactory(
            user=owner,
            card=card,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_comment(
        self,
        api_client,
        own_comment,
    ):
        url = reverse("comment-detail", args=[own_comment.pk])

        response = api_client.delete(url)

        assert response.status_code == 401
        assert Comment.objects.filter(pk=own_comment.pk).exists()

    # ---------------------------------------------------------
    # Comment owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_comment_owner_can_delete_comment(
        self,
        mock_log,
        api_client,
        user,
        own_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[own_comment.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not Comment.objects.filter(pk=own_comment.pk).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == own_comment.card.board_list.board
        assert kwargs["board_list"] == own_comment.card.board_list
        assert kwargs["card"] == own_comment.card
        assert kwargs["action_type"] == "remove_comment"
        assert kwargs["text"] == (
            f"'{user.username}' remove his comment"
        )

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_cannot_delete_other_users_comment(
        self,
        mock_log,
        api_client,
        owner_not_comment_owner,
    ):
        board_owner, comment = owner_not_comment_owner

        api_client.force_authenticate(board_owner)

        url = reverse("comment-detail", args=[comment.pk])

        response = api_client.delete(url)

        assert response.status_code == 403

        assert Comment.objects.filter(pk=comment.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_cannot_delete_other_users_comment(
        self,
        mock_log,
        api_client,
        member_not_comment_owner,
    ):
        member, comment = member_not_comment_owner

        api_client.force_authenticate(member)

        url = reverse("comment-detail", args=[comment.pk])

        response = api_client.delete(url)

        assert response.status_code == 403

        assert Comment.objects.filter(pk=comment.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_delete_comment_outside_his_boards(
        self,
        api_client,
        user,
        stranger_comment,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[stranger_comment.pk])

        response = api_client.delete(url)

        assert response.status_code == 404

        assert Comment.objects.filter(pk=stranger_comment.pk).exists()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_comment_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("comment-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End CommentViewSet Tests
#======================


#======================
#  Start CardFileViewSet Tests
#======================


@pytest.mark.django_db
class TestCardFileListView:
    """Tests for CardFileViewSet.list()."""

    @pytest.fixture
    def url(self):
        return reverse("cardfile-list")

    @pytest.fixture
    def owner_files(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardFileFactory.create_batch(
            3,
            card=card,
            user=user,
        )

    @pytest.fixture
    def member_files(self, user):
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

        return CardFileFactory.create_batch(
            2,
            card=card,
            user=owner,
        )

    @pytest.fixture
    def stranger_files(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardFileFactory.create_batch(
            4,
            card=card,
            user=owner,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_files(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    def test_board_owner_can_list_files(
        self,
        api_client,
        user,
        url,
        owner_files,
        stranger_files,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {obj.id for obj in owner_files}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Member
    # ---------------------------------------------------------

    def test_board_member_can_list_files(
        self,
        api_client,
        user,
        url,
        member_files,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {obj.id for obj in member_files}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_files_from_other_boards_are_not_returned(
        self,
        api_client,
        user,
        url,
        owner_files,
        stranger_files,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {item["id"] for item in response.data}
        stranger_ids = {obj.id for obj in stranger_files}

        assert returned_ids.isdisjoint(stranger_ids)

    # ---------------------------------------------------------
    # Distinct
    # ---------------------------------------------------------

    def test_list_contains_no_duplicates(
        self,
        api_client,
        user,
        url,
        owner_files,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        ids = [item["id"] for item in response.data]

        assert len(ids) == len(set(ids))

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        url,
        owner_files,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data[0].keys()) == {
            "id", "name", "display_name","description", "file", "file_type", "upload_at", "user", "card"
        }



@pytest.mark.django_db
class TestCardFileRetrieveView:
    """Tests for CardFileViewSet.retrieve()."""

    @pytest.fixture
    def owner_file(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardFileFactory(
            card=card,
            user=user,
        )

    @pytest.fixture
    def member_file(self, user):
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

        return CardFileFactory(
            card=card,
            user=owner,
        )

    @pytest.fixture
    def stranger_file(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardFileFactory(
            card=card,
            user=owner,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_file(
        self,
        api_client,
        owner_file,
    ):
        url = reverse("cardfile-detail", args=[owner_file.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_retrieve_file(
        self,
        api_client,
        user,
        owner_file,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[owner_file.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_file.id
        assert response.data["card"] == owner_file.card.id
        assert response.data["user"] == user.id

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_file(
        self,
        api_client,
        user,
        member_file,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[member_file.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_file.id
        assert response.data["card"] == member_file.card.id

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_file_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_file,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[stranger_file.pk])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_retrieve_nonexistent_file_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404



@pytest.mark.django_db
class TestCardFileCreateView:
    """Tests for CardFileViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("cardfile-list")

    @pytest.fixture
    def uploaded_file(self):
        return SimpleUploadedFile(
            "document.txt",
            b"hello world",
            content_type="text/plain",
        )

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

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_attachment(
        self,
        api_client,
        url,
        owner_card,
        uploaded_file,
    ):
        response = api_client.post(
            url,
            {
                "card": owner_card.id,
                "file": uploaded_file,
            },
            format="multipart",
        )

        assert response.status_code == 401
        assert CardFile.objects.count() == 0

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_create_attachment(
        self,
        mock_log,
        api_client,
        user,
        url,
        owner_card,
        uploaded_file,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": owner_card.id,
                "file": uploaded_file,
            },
            format="multipart",
        )

        assert response.status_code == 201

        attachment = CardFile.objects.get()

        assert attachment.user == user
        assert attachment.card == owner_card

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_card.board_list.board
        assert kwargs["board_list"] == owner_card.board_list
        assert kwargs["card"] == owner_card
        assert kwargs["action_type"] == "add_attachment"

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_attachment(
        self,
        mock_log,
        api_client,
        user,
        url,
        member_card,
        uploaded_file,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": member_card.id,
                "file": uploaded_file,
            },
            format="multipart",
        )

        assert response.status_code == 201

        attachment = CardFile.objects.get()

        assert attachment.user == user
        assert attachment.card == member_card

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_create_attachment_for_unrelated_card(
        self,
        api_client,
        user,
        url,
        stranger_card,
        uploaded_file,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": stranger_card.id,
                "file": uploaded_file,
            },
            format="multipart",
        )

        assert response.status_code == 403
        assert CardFile.objects.count() == 0

    def test_missing_card_returns_403(
        self,
        api_client,
        user,
        url,
        uploaded_file,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "file": uploaded_file,
            },
            format="multipart",
        )

        assert response.status_code == 403
        assert CardFile.objects.count() == 0

    def test_invalid_card_returns_403(
        self,
        api_client,
        user,
        url,
        uploaded_file,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": 999999,
                "file": uploaded_file,
            },
            format="multipart",
        )

        assert response.status_code == 403
        assert CardFile.objects.count() == 0

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_file_is_required(
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
            format="multipart",
        )

        assert response.status_code == 400
        assert "file" in response.data

        assert CardFile.objects.count() == 0


@pytest.mark.django_db
class TestCardFileUpdateView:
    """Tests for CardFileViewSet.update()."""

    @pytest.fixture
    def own_attachment(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardFileFactory(
            user=user,
            card=card,
        )

    @pytest.fixture
    def owner_not_attachment_owner(self):
        """
        Board owner attempts to update another user's attachment.
        """
        board_owner = UserFactory()
        attachment_owner = UserFactory()

        board = BoardFactory(owner=board_owner)

        BoardMembership.objects.create(
            board=board,
            user=attachment_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        attachment = CardFileFactory(
            user=attachment_owner,
            card=card,
        )

        return board_owner, attachment

    @pytest.fixture
    def member_not_attachment_owner(self):
        """
        Board member attempts to update another member's attachment.
        """
        owner = UserFactory()
        member = UserFactory()
        attachment_owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=member,
            member_type="member",
            accepted=True,
        )

        BoardMembership.objects.create(
            board=board,
            user=attachment_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        attachment = CardFileFactory(
            user=attachment_owner,
            card=card,
        )

        return member, attachment

    @pytest.fixture
    def stranger_attachment(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardFileFactory(
            user=owner,
            card=card,
        )

    @pytest.fixture
    def new_file(self):
        return SimpleUploadedFile(
            "updated.txt",
            b"updated file",
            content_type="text/plain",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_attachment(
        self,
        api_client,
        own_attachment,
        new_file,
    ):
        url = reverse("cardfile-detail", args=[own_attachment.pk])

        response = api_client.patch(
            url,
            {"file": new_file},
            format="multipart",
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Attachment owner
    # ---------------------------------------------------------

    def test_attachment_owner_can_update_attachment(
        self,
        api_client,
        user,
        own_attachment,
        new_file,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[own_attachment.pk])

        response = api_client.patch(
            url,
            {"file": new_file},
            format="multipart",
        )

        assert response.status_code == 200

        own_attachment.refresh_from_db()

        assert own_attachment.file.name.endswith("updated.txt")

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_cannot_update_other_users_attachment(
        self,
        api_client,
        owner_not_attachment_owner,
        new_file,
    ):
        board_owner, attachment = owner_not_attachment_owner

        api_client.force_authenticate(board_owner)

        url = reverse("cardfile-detail", args=[attachment.pk])

        response = api_client.patch(
            url,
            {"file": new_file},
            format="multipart",
        )

        assert response.status_code == 403

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_cannot_update_other_users_attachment(
        self,
        api_client,
        member_not_attachment_owner,
        new_file,
    ):
        member, attachment = member_not_attachment_owner

        api_client.force_authenticate(member)

        url = reverse("cardfile-detail", args=[attachment.pk])

        response = api_client.patch(
            url,
            {"file": new_file},
            format="multipart",
        )

        assert response.status_code == 403

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_update_attachment_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_attachment,
        new_file,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[stranger_attachment.pk])

        response = api_client.patch(
            url,
            {"file": new_file},
            format="multipart",
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_update_nonexistent_attachment_returns_404(
        self,
        api_client,
        user,
        new_file,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[999999])

        response = api_client.patch(
            url,
            {"file": new_file},
            format="multipart",
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCardFileDestroyView:
    """Tests for CardFileViewSet.destroy()."""

    @pytest.fixture
    def own_attachment(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardFileFactory(
            user=user,
            card=card,
        )

    @pytest.fixture
    def owner_not_attachment_owner(self):
        """
        Board owner attempts to delete another user's attachment.
        """
        board_owner = UserFactory()
        attachment_owner = UserFactory()

        board = BoardFactory(owner=board_owner)

        BoardMembership.objects.create(
            board=board,
            user=attachment_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        attachment = CardFileFactory(
            user=attachment_owner,
            card=card,
        )

        return board_owner, attachment

    @pytest.fixture
    def member_not_attachment_owner(self):
        """
        Board member attempts to delete another member's attachment.
        """
        owner = UserFactory()
        member = UserFactory()
        attachment_owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=member,
            member_type="member",
            accepted=True,
        )

        BoardMembership.objects.create(
            board=board,
            user=attachment_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        attachment = CardFileFactory(
            user=attachment_owner,
            card=card,
        )

        return member, attachment

    @pytest.fixture
    def stranger_attachment(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardFileFactory(
            user=owner,
            card=card,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_attachment(
        self,
        api_client,
        own_attachment,
    ):
        url = reverse("cardfile-detail", args=[own_attachment.pk])

        response = api_client.delete(url)

        assert response.status_code == 401
        assert CardFile.objects.filter(pk=own_attachment.pk).exists()

    # ---------------------------------------------------------
    # Attachment owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_attachment_owner_can_delete_attachment(
        self,
        mock_log,
        api_client,
        user,
        own_attachment,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[own_attachment.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not CardFile.objects.filter(pk=own_attachment.pk).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == own_attachment.card.board_list.board
        assert kwargs["board_list"] == own_attachment.card.board_list
        assert kwargs["card"] == own_attachment.card
        assert kwargs["action_type"] == "remove_attachment"
        assert kwargs["text"] == (
            f"The '{own_attachment.get_name()}' attachment in "
            f"'{own_attachment.card.name}' card was removed"
        )

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_cannot_delete_other_users_attachment(
        self,
        mock_log,
        api_client,
        owner_not_attachment_owner,
    ):
        board_owner, attachment = owner_not_attachment_owner

        api_client.force_authenticate(board_owner)

        url = reverse("cardfile-detail", args=[attachment.pk])

        response = api_client.delete(url)

        assert response.status_code == 403
        assert CardFile.objects.filter(pk=attachment.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_cannot_delete_other_users_attachment(
        self,
        mock_log,
        api_client,
        member_not_attachment_owner,
    ):
        member, attachment = member_not_attachment_owner

        api_client.force_authenticate(member)

        url = reverse("cardfile-detail", args=[attachment.pk])

        response = api_client.delete(url)

        assert response.status_code == 403
        assert CardFile.objects.filter(pk=attachment.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_delete_attachment_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_attachment,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[stranger_attachment.pk])

        response = api_client.delete(url)

        assert response.status_code == 404

        assert CardFile.objects.filter(pk=stranger_attachment.pk).exists()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_attachment_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardfile-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End CardFileViewSet Tests
#======================


#======================
#  Start CardImageViewSet Tests
#======================

@pytest.mark.django_db
class TestCardImageListView:
    """Tests for CardImageViewSet.list()."""

    @pytest.fixture
    def url(self):
        return reverse("cardimage-list")

    @pytest.fixture
    def owner_images(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardImageFactory.create_batch(
            3,
            card=card,
            user=user,
        )

    @pytest.fixture
    def member_images(self, user):
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

        return CardImageFactory.create_batch(
            2,
            card=card,
            user=owner,
        )

    @pytest.fixture
    def stranger_images(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardImageFactory.create_batch(
            4,
            card=card,
            user=owner,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_images(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_list_images(
        self,
        api_client,
        user,
        url,
        owner_images,
        stranger_images,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {obj.id for obj in owner_images}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_list_images(
        self,
        api_client,
        user,
        url,
        member_images,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {obj.id for obj in member_images}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_images_from_other_boards_are_not_returned(
        self,
        api_client,
        user,
        url,
        owner_images,
        stranger_images,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {item["id"] for item in response.data}
        stranger_ids = {obj.id for obj in stranger_images}

        assert returned_ids.isdisjoint(stranger_ids)

    # ---------------------------------------------------------
    # Distinct
    # ---------------------------------------------------------

    def test_list_contains_no_duplicates(
        self,
        api_client,
        user,
        url,
        owner_images,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        ids = [item["id"] for item in response.data]

        assert len(ids) == len(set(ids))

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        url,
        owner_images,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data[0].keys()) == {
            "id", "name", "display_name","description", "file", "file_type", "upload_at", "user", "card"

        }



@pytest.mark.django_db
class TestCardImageRetrieveView:
    """Tests for CardImageViewSet.retrieve()."""

    @pytest.fixture
    def owner_image(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardImageFactory(
            card=card,
            user=user,
        )

    @pytest.fixture
    def member_image(self, user):
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

        return CardImageFactory(
            card=card,
            user=owner,
        )

    @pytest.fixture
    def stranger_image(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardImageFactory(
            card=card,
            user=owner,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_image(
        self,
        api_client,
        owner_image,
    ):
        url = reverse("cardimage-detail", args=[owner_image.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_retrieve_image(
        self,
        api_client,
        user,
        owner_image,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[owner_image.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_image.id
        assert response.data["card"] == owner_image.card.id
        assert response.data["user"] == user.id

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_image(
        self,
        api_client,
        user,
        member_image,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[member_image.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_image.id
        assert response.data["card"] == member_image.card.id

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_image_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_image,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[stranger_image.pk])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_retrieve_nonexistent_image_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404



@pytest.mark.django_db
class TestCardImageCreateView:
    """Tests for CardImageViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("cardimage-list")

    @pytest.fixture
    def uploaded_image(self):
        """
        Return a valid in-memory PNG image.
        """
        image = Image.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return SimpleUploadedFile(
            "test.png",
            buffer.read(),
            content_type="image/png",
        )

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

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_image(
        self,
        api_client,
        url,
        owner_card,
        uploaded_image,
    ):
        response = api_client.post(
            url,
            {
                "card": owner_card.id,
                "file": uploaded_image,
            },
            format="multipart",
        )

        assert response.status_code == 401
        assert CardImage.objects.count() == 0

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_create_image(
        self,
        mock_log,
        api_client,
        user,
        url,
        owner_card,
        uploaded_image,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": owner_card.id,
                "file": uploaded_image,
            },
            format="multipart",
        )

        assert response.status_code == 201

        attachment = CardImage.objects.get()

        assert attachment.user == user
        assert attachment.card == owner_card

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_card.board_list.board
        assert kwargs["board_list"] == owner_card.board_list
        assert kwargs["card"] == owner_card
        assert kwargs["action_type"] == "add_attachment"

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_image(
        self,
        mock_log,
        api_client,
        user,
        url,
        member_card,
        uploaded_image,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": member_card.id,
                "file": uploaded_image,
            },
            format="multipart",
        )

        assert response.status_code == 201

        attachment = CardImage.objects.get()

        assert attachment.user == user
        assert attachment.card == member_card

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_create_image_for_unrelated_card(
        self,
        api_client,
        user,
        url,
        stranger_card,
        uploaded_image,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": stranger_card.id,
                "file": uploaded_image,
            },
            format="multipart",
        )

        assert response.status_code == 403
        assert CardImage.objects.count() == 0

    def test_missing_card_returns_403(
        self,
        api_client,
        user,
        url,
        uploaded_image,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "file": uploaded_image,
            },
            format="multipart",
        )

        assert response.status_code == 403
        assert CardImage.objects.count() == 0

    def test_invalid_card_returns_403(
        self,
        api_client,
        user,
        url,
        uploaded_image,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "card": 999999,
                "file": uploaded_image,
            },
            format="multipart",
        )

        assert response.status_code == 403
        assert CardImage.objects.count() == 0

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_image_is_required(
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
            format="multipart",
        )

        assert response.status_code == 400
        assert "file" in response.data

        assert CardImage.objects.count() == 0


@pytest.mark.django_db
class TestCardImageUpdateView:
    """Tests for CardImageViewSet.update()."""

    @pytest.fixture
    def updated_image(self):
        image = Image.new("RGB", (200, 200), color="blue")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return SimpleUploadedFile(
            "updated.png",
            buffer.read(),
            content_type="image/png",
        )

    @pytest.fixture
    def own_image(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardImageFactory(
            user=user,
            card=card,
        )

    @pytest.fixture
    def owner_not_image_owner(self):
        """
        Board owner attempts to update another user's image.
        """
        board_owner = UserFactory()
        image_owner = UserFactory()

        board = BoardFactory(owner=board_owner)

        BoardMembership.objects.create(
            board=board,
            user=image_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        image = CardImageFactory(
            user=image_owner,
            card=card,
        )

        return board_owner, image

    @pytest.fixture
    def member_not_image_owner(self):
        """
        Board member attempts to update another member's image.
        """
        owner = UserFactory()
        member = UserFactory()
        image_owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=member,
            member_type="member",
            accepted=True,
        )

        BoardMembership.objects.create(
            board=board,
            user=image_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        image = CardImageFactory(
            user=image_owner,
            card=card,
        )

        return member, image

    @pytest.fixture
    def stranger_image(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardImageFactory(
            user=owner,
            card=card,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_image(
        self,
        api_client,
        own_image,
        updated_image,
    ):
        url = reverse("cardimage-detail", args=[own_image.pk])

        response = api_client.patch(
            url,
            {"file": updated_image},
            format="multipart",
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Image owner
    # ---------------------------------------------------------

    def test_image_owner_can_update_image(
        self,
        api_client,
        user,
        own_image,
        updated_image,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[own_image.pk])

        response = api_client.patch(
            url,
            {"file": updated_image},
            format="multipart",
        )

        assert response.status_code == 200

        own_image.refresh_from_db()

        assert own_image.file.name.endswith("updated.png")

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_cannot_update_other_users_image(
        self,
        api_client,
        owner_not_image_owner,
        updated_image,
    ):
        board_owner, image = owner_not_image_owner

        api_client.force_authenticate(board_owner)

        url = reverse("cardimage-detail", args=[image.pk])

        response = api_client.patch(
            url,
            {"file": updated_image},
            format="multipart",
        )

        assert response.status_code == 403

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_cannot_update_other_users_image(
        self,
        api_client,
        member_not_image_owner,
        updated_image,
    ):
        member, image = member_not_image_owner

        api_client.force_authenticate(member)

        url = reverse("cardimage-detail", args=[image.pk])

        response = api_client.patch(
            url,
            {"file": updated_image},
            format="multipart",
        )

        assert response.status_code == 403

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_update_image_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_image,
        updated_image,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[stranger_image.pk])

        response = api_client.patch(
            url,
            {"file": updated_image},
            format="multipart",
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_update_nonexistent_image_returns_404(
        self,
        api_client,
        user,
        updated_image,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[999999])

        response = api_client.patch(
            url,
            {"file": updated_image},
            format="multipart",
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCardImageDestroyView:
    """Tests for CardImageViewSet.destroy()."""

    @pytest.fixture
    def own_image(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardImageFactory(
            user=user,
            card=card,
        )

    @pytest.fixture
    def owner_not_image_owner(self):
        """
        Board owner attempts to delete another user's image.
        """
        board_owner = UserFactory()
        image_owner = UserFactory()

        board = BoardFactory(owner=board_owner)

        BoardMembership.objects.create(
            board=board,
            user=image_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        image = CardImageFactory(
            user=image_owner,
            card=card,
        )

        return board_owner, image

    @pytest.fixture
    def member_not_image_owner(self):
        """
        Board member attempts to delete another member's image.
        """
        owner = UserFactory()
        member = UserFactory()
        image_owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=member,
            member_type="member",
            accepted=True,
        )

        BoardMembership.objects.create(
            board=board,
            user=image_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        image = CardImageFactory(
            user=image_owner,
            card=card,
        )

        return member, image

    @pytest.fixture
    def stranger_image(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardImageFactory(
            user=owner,
            card=card,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_image(
        self,
        api_client,
        own_image,
    ):
        url = reverse("cardimage-detail", args=[own_image.pk])

        response = api_client.delete(url)

        assert response.status_code == 401
        assert CardImage.objects.filter(pk=own_image.pk).exists()

    # ---------------------------------------------------------
    # Image owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_image_owner_can_delete_image(
        self,
        mock_log,
        api_client,
        user,
        own_image,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[own_image.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not CardImage.objects.filter(pk=own_image.pk).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == own_image.card.board_list.board
        assert kwargs["board_list"] == own_image.card.board_list
        assert kwargs["card"] == own_image.card
        assert kwargs["action_type"] == "remove_attachment"
        assert kwargs["text"] == (
            f"The '{own_image.get_name()}' attachment in "
            f"'{own_image.card.name}' card was removed"
        )

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_cannot_delete_other_users_image(
        self,
        mock_log,
        api_client,
        owner_not_image_owner,
    ):
        board_owner, image = owner_not_image_owner

        api_client.force_authenticate(board_owner)

        url = reverse("cardimage-detail", args=[image.pk])

        response = api_client.delete(url)

        assert response.status_code == 403

        assert CardImage.objects.filter(pk=image.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_cannot_delete_other_users_image(
        self,
        mock_log,
        api_client,
        member_not_image_owner,
    ):
        member, image = member_not_image_owner

        api_client.force_authenticate(member)

        url = reverse("cardimage-detail", args=[image.pk])

        response = api_client.delete(url)

        assert response.status_code == 403

        assert CardImage.objects.filter(pk=image.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_delete_image_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_image,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[stranger_image.pk])

        response = api_client.delete(url)

        assert response.status_code == 404

        assert CardImage.objects.filter(pk=stranger_image.pk).exists()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_image_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardimage-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404

#======================
#  End CardImageViewSet Tests
#======================


#======================
#  Start LinkAttachmentViewSet Tests
#======================


@pytest.mark.django_db
class TestLinkAttachmentListView:
    """Tests for LinkAttachmentViewSet.list()."""

    @pytest.fixture
    def url(self):
        return reverse("linkattachment-list")

    @pytest.fixture
    def owner_links(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return LinkAttachmentFactory.create_batch(
            3,
            card=card,
            user=user,
        )

    @pytest.fixture
    def member_links(self, user):
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

        return LinkAttachmentFactory.create_batch(
            2,
            card=card,
            user=owner,
        )

    @pytest.fixture
    def stranger_links(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return LinkAttachmentFactory.create_batch(
            4,
            card=card,
            user=owner,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_links(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_list_links(
        self,
        api_client,
        user,
        url,
        owner_links,
        stranger_links,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {obj.id for obj in owner_links}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_list_links(
        self,
        api_client,
        user,
        url,
        member_links,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {obj.id for obj in member_links}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_links_from_other_boards_are_not_returned(
        self,
        api_client,
        user,
        url,
        owner_links,
        stranger_links,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {item["id"] for item in response.data}
        stranger_ids = {obj.id for obj in stranger_links}

        assert returned_ids.isdisjoint(stranger_ids)

    # ---------------------------------------------------------
    # Distinct
    # ---------------------------------------------------------

    def test_list_contains_no_duplicates(
        self,
        api_client,
        user,
        url,
        owner_links,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        ids = [item["id"] for item in response.data]

        assert len(ids) == len(set(ids))

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        url,
        owner_links,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data[0].keys()) == {
            "id", "name", "display_name","description", "file", "file_type", "upload_at", "user", "card"

        }


@pytest.mark.django_db
class TestLinkAttachmentRetrieveView:
    """Tests for LinkAttachmentViewSet.retrieve()."""

    @pytest.fixture
    def owner_link(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return LinkAttachmentFactory(
            user=user,
            card=card,
        )

    @pytest.fixture
    def member_link(self, user):
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

        return LinkAttachmentFactory(
            user=owner,
            card=card,
        )

    @pytest.fixture
    def stranger_link(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return LinkAttachmentFactory(
            user=owner,
            card=card,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_link(
        self,
        api_client,
        owner_link,
    ):
        url = reverse("linkattachment-detail", args=[owner_link.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_retrieve_link(
        self,
        api_client,
        user,
        owner_link,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[owner_link.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_link.id
        assert response.data["card"] == owner_link.card.id
        assert response.data["user"] == user.id
        assert response.data["file"] == owner_link.file

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_link(
        self,
        api_client,
        user,
        member_link,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[member_link.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_link.id
        assert response.data["card"] == member_link.card.id
        assert response.data["user"] == member_link.user.id
        assert response.data["file"] == member_link.file

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_link_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_link,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[stranger_link.pk])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_retrieve_nonexistent_link_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestLinkAttachmentCreateView:
    """Tests for LinkAttachmentViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("linkattachment-list")

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
            "card": owner_card.id,
            "file": "https://example.com/document.pdf",
        }

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_link(
        self,
        api_client,
        url,
        valid_data,
    ):
        response = api_client.post(url, valid_data)

        assert response.status_code == 401
        assert LinkAttachment.objects.count() == 0

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_create_link(
        self,
        mock_log,
        api_client,
        user,
        url,
        valid_data,
        owner_card,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(url, valid_data)

        assert response.status_code == 201

        attachment = LinkAttachment.objects.get()

        assert attachment.user == user
        assert attachment.card == owner_card
        assert attachment.file == valid_data["file"]

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_card.board_list.board
        assert kwargs["board_list"] == owner_card.board_list
        assert kwargs["card"] == owner_card
        assert kwargs["action_type"] == "add_attachment"

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_link(
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
                "card": member_card.id,
                "file": "https://example.com/image.png",
            },
        )

        assert response.status_code == 201

        attachment = LinkAttachment.objects.get()

        assert attachment.user == user
        assert attachment.card == member_card

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_create_link_for_unrelated_card(
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
                "card": stranger_card.id,
                "file": "https://example.com/file.pdf",
            },
        )

        assert response.status_code == 403
        assert LinkAttachment.objects.count() == 0

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
                "file": "https://example.com/file.pdf",
            },
        )

        assert response.status_code == 403
        assert LinkAttachment.objects.count() == 0

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
                "card": 999999,
                "file": "https://example.com/file.pdf",
            },
        )

        assert response.status_code == 403
        assert LinkAttachment.objects.count() == 0

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_file_is_required(
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
        )

        assert response.status_code == 400
        assert "file" in response.data

        assert LinkAttachment.objects.count() == 0


@pytest.mark.django_db
class TestLinkAttachmentUpdateView:
    """Tests for LinkAttachmentViewSet.update()."""

    @pytest.fixture
    def own_link(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return LinkAttachmentFactory(
            user=user,
            card=card,
            file="https://example.com/old.pdf",
        )

    @pytest.fixture
    def owner_not_link_owner(self):
        """
        Board owner attempts to update another user's link.
        """
        board_owner = UserFactory()
        link_owner = UserFactory()

        board = BoardFactory(owner=board_owner)

        BoardMembership.objects.create(
            board=board,
            user=link_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        link = LinkAttachmentFactory(
            user=link_owner,
            card=card,
            file="https://example.com/old.pdf",
        )

        return board_owner, link

    @pytest.fixture
    def member_not_link_owner(self):
        """
        Board member attempts to update another member's link.
        """
        owner = UserFactory()
        member = UserFactory()
        link_owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=member,
            member_type="member",
            accepted=True,
        )

        BoardMembership.objects.create(
            board=board,
            user=link_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        link = LinkAttachmentFactory(
            user=link_owner,
            card=card,
            file="https://example.com/old.pdf",
        )

        return member, link

    @pytest.fixture
    def stranger_link(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return LinkAttachmentFactory(
            user=owner,
            card=card,
            file="https://example.com/old.pdf",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_link(
        self,
        api_client,
        own_link,
    ):
        url = reverse("linkattachment-detail", args=[own_link.pk])

        response = api_client.patch(
            url,
            {
                "file": "https://example.com/new.pdf",
            },
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Link owner
    # ---------------------------------------------------------

    def test_link_owner_can_update_link(
        self,
        api_client,
        user,
        own_link,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[own_link.pk])

        new_url = "https://example.com/new.pdf"

        response = api_client.patch(
            url,
            {
                "file": new_url,
            },
        )

        assert response.status_code == 200

        own_link.refresh_from_db()

        assert own_link.file == new_url

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_cannot_update_other_users_link(
        self,
        api_client,
        owner_not_link_owner,
    ):
        board_owner, link = owner_not_link_owner

        api_client.force_authenticate(board_owner)

        url = reverse("linkattachment-detail", args=[link.pk])

        response = api_client.patch(
            url,
            {
                "file": "https://example.com/new.pdf",
            },
        )

        assert response.status_code == 403

        link.refresh_from_db()

        assert link.file == "https://example.com/old.pdf"

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_cannot_update_other_users_link(
        self,
        api_client,
        member_not_link_owner,
    ):
        member, link = member_not_link_owner

        api_client.force_authenticate(member)

        url = reverse("linkattachment-detail", args=[link.pk])

        response = api_client.patch(
            url,
            {
                "file": "https://example.com/new.pdf",
            },
        )

        assert response.status_code == 403

        link.refresh_from_db()

        assert link.file == "https://example.com/old.pdf"

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_update_link_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_link,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[stranger_link.pk])

        response = api_client.patch(
            url,
            {
                "file": "https://example.com/new.pdf",
            },
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_update_nonexistent_link_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[999999])

        response = api_client.patch(
            url,
            {
                "file": "https://example.com/new.pdf",
            },
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestLinkAttachmentDestroyView:
    """Tests for LinkAttachmentViewSet.destroy()."""

    @pytest.fixture
    def own_link(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return LinkAttachmentFactory(
            user=user,
            card=card,
            file="https://example.com/document.pdf",
        )

    @pytest.fixture
    def owner_not_link_owner(self):
        """
        Board owner attempts to delete another user's link.
        """
        board_owner = UserFactory()
        link_owner = UserFactory()

        board = BoardFactory(owner=board_owner)

        BoardMembership.objects.create(
            board=board,
            user=link_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        link = LinkAttachmentFactory(
            user=link_owner,
            card=card,
            file="https://example.com/document.pdf",
        )

        return board_owner, link

    @pytest.fixture
    def member_not_link_owner(self):
        """
        Board member attempts to delete another member's link.
        """
        owner = UserFactory()
        member = UserFactory()
        link_owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=member,
            member_type="member",
            accepted=True,
        )

        BoardMembership.objects.create(
            board=board,
            user=link_owner,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        link = LinkAttachmentFactory(
            user=link_owner,
            card=card,
            file="https://example.com/document.pdf",
        )

        return member, link

    @pytest.fixture
    def stranger_link(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return LinkAttachmentFactory(
            user=owner,
            card=card,
            file="https://example.com/document.pdf",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_link(
        self,
        api_client,
        own_link,
    ):
        url = reverse("linkattachment-detail", args=[own_link.pk])

        response = api_client.delete(url)

        assert response.status_code == 401
        assert LinkAttachment.objects.filter(pk=own_link.pk).exists()

    # ---------------------------------------------------------
    # Link owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_link_owner_can_delete_link(
        self,
        mock_log,
        api_client,
        user,
        own_link,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[own_link.pk])

        response = api_client.delete(url)

        assert response.status_code == 204
        assert not LinkAttachment.objects.filter(pk=own_link.pk).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == own_link.card.board_list.board
        assert kwargs["board_list"] == own_link.card.board_list
        assert kwargs["card"] == own_link.card
        assert kwargs["action_type"] == "remove_attachment"
        assert kwargs["text"] == (
            f"The '{own_link.file}' link in "
            f"'{own_link.card.name}' card was removed"
        )

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_cannot_delete_other_users_link(
        self,
        mock_log,
        api_client,
        owner_not_link_owner,
    ):
        board_owner, link = owner_not_link_owner

        api_client.force_authenticate(board_owner)

        url = reverse("linkattachment-detail", args=[link.pk])

        response = api_client.delete(url)

        assert response.status_code == 403
        assert LinkAttachment.objects.filter(pk=link.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_cannot_delete_other_users_link(
        self,
        mock_log,
        api_client,
        member_not_link_owner,
    ):
        member, link = member_not_link_owner

        api_client.force_authenticate(member)

        url = reverse("linkattachment-detail", args=[link.pk])

        response = api_client.delete(url)

        assert response.status_code == 403
        assert LinkAttachment.objects.filter(pk=link.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_delete_link_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_link,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[stranger_link.pk])

        response = api_client.delete(url)

        assert response.status_code == 404
        assert LinkAttachment.objects.filter(pk=stranger_link.pk).exists()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_link_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("linkattachment-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End LinkAttachmentViewSet Tests
#======================


#======================
#  Start CardLabelViewSet Tests
#======================


@pytest.mark.django_db
class TestCardLabelListView:
    """Tests for CardLabelViewSet.list()."""

    @pytest.fixture
    def url(self):
        return reverse("cardlabel-list")

    @pytest.fixture
    def owner_labels(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardLabelFactory.create_batch(
            3,
            card=card,
        )

    @pytest.fixture
    def member_labels(self, user):
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

        return CardLabelFactory.create_batch(
            2,
            card=card,
        )

    @pytest.fixture
    def stranger_labels(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardLabelFactory.create_batch(
            4,
            card=card,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_labels(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_list_labels(
        self,
        api_client,
        user,
        url,
        owner_labels,
        stranger_labels,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {label.id for label in owner_labels}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_list_labels(
        self,
        api_client,
        user,
        url,
        member_labels,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {label.id for label in member_labels}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_labels_from_other_boards_are_not_returned(
        self,
        api_client,
        user,
        url,
        owner_labels,
        stranger_labels,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {item["id"] for item in response.data}
        stranger_ids = {label.id for label in stranger_labels}

        assert returned_ids.isdisjoint(stranger_ids)

    # ---------------------------------------------------------
    # Distinct
    # ---------------------------------------------------------

    def test_list_contains_no_duplicates(
        self,
        api_client,
        user,
        url,
        owner_labels,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        ids = [item["id"] for item in response.data]

        assert len(ids) == len(set(ids))

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        url,
        owner_labels,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data[0].keys()) == {
            "id",
            "card",
            "name",
            "color",
        }


@pytest.mark.django_db
class TestCardLabelRetrieveView:
    """Tests for CardLabelViewSet.retrieve()."""

    @pytest.fixture
    def owner_label(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardLabelFactory(card=card)

    @pytest.fixture
    def member_label(self, user):
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

        return CardLabelFactory(card=card)

    @pytest.fixture
    def stranger_label(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardLabelFactory(card=card)

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_label(
        self,
        api_client,
        owner_label,
    ):
        url = reverse("cardlabel-detail", args=[owner_label.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_retrieve_label(
        self,
        api_client,
        user,
        owner_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[owner_label.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_label.id
        assert response.data["card"] == owner_label.card.id
        assert response.data["name"] == owner_label.name
        assert response.data["color"] == owner_label.color

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_label(
        self,
        api_client,
        user,
        member_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[member_label.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_label.id
        assert response.data["card"] == member_label.card.id
        assert response.data["name"] == member_label.name
        assert response.data["color"] == member_label.color

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_label_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[stranger_label.pk])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_retrieve_nonexistent_label_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestCardLabelCreateView:
    """Tests for CardLabelViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("cardlabel-list")

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
            "card": owner_card.id,
            "name": "Bug",
            "color": "#ff0000",
        }

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_label(
        self,
        api_client,
        url,
        valid_data,
    ):
        response = api_client.post(url, valid_data)

        assert response.status_code == 401
        assert CardLabel.objects.count() == 0

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_create_label(
        self,
        mock_log,
        api_client,
        user,
        url,
        valid_data,
        owner_card,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(url, valid_data)

        assert response.status_code == 201

        label = CardLabel.objects.get()

        assert label.card == owner_card
        assert label.name == valid_data["name"]
        assert label.color == valid_data["color"]

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_card.board_list.board
        assert kwargs["board_list"] == owner_card.board_list
        assert kwargs["card"] == owner_card
        assert kwargs["action_type"] == "add_card_label"
        assert kwargs["text"] == (
            f"'{label.name}' label added to'{owner_card.name}' card"
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_label(
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
                "card": member_card.id,
                "name": "Feature",
                "color": "#00ff00",
            },
        )

        assert response.status_code == 201

        label = CardLabel.objects.get()

        assert label.card == member_card
        assert label.name == "Feature"

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_create_label_for_unrelated_card(
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
                "card": stranger_card.id,
                "name": "Bug",
                "color": "#ff0000",
            },
        )

        assert response.status_code == 403
        assert CardLabel.objects.count() == 0

    def test_missing_card_returns_400(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "Bug",
                "color": "#ff0000",
            },
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
                "card": 999999,
                "name": "Bug",
                "color": "#ff0000",
            },
        )

        assert response.status_code == 403
        assert CardLabel.objects.count() == 0

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    @pytest.mark.parametrize("missing_field", ["name", "color"])
    def test_required_fields(
        self,
        api_client,
        user,
        url,
        valid_data,
        missing_field,
    ):
        api_client.force_authenticate(user)

        data = valid_data.copy()
        data.pop(missing_field)

        response = api_client.post(url, data)

        assert response.status_code == 400
        assert missing_field in response.data

        assert CardLabel.objects.count() == 0


@pytest.mark.django_db
class TestCardLabelUpdateView:
    """Tests for CardLabelViewSet.update()."""

    @pytest.fixture
    def owner_label(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardLabelFactory(
            card=card,
            name="Bug",
            color="#ff0000",
        )

    @pytest.fixture
    def member_label(self, user):
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

        return CardLabelFactory(
            card=card,
            name="Bug",
            color="#ff0000",
        )

    @pytest.fixture
    def stranger_label(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardLabelFactory(
            card=card,
            name="Bug",
            color="#ff0000",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_label(
        self,
        api_client,
        owner_label,
    ):
        url = reverse("cardlabel-detail", args=[owner_label.pk])

        response = api_client.patch(
            url,
            {
                "name": "Feature",
            },
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_update_label(
        self,
        api_client,
        user,
        owner_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[owner_label.pk])

        response = api_client.patch(
            url,
            {
                "name": "Feature",
                "color": "#00ff00",
            },
        )

        assert response.status_code == 200

        owner_label.refresh_from_db()

        assert owner_label.name == "Feature"
        assert owner_label.color == "#00ff00"

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_update_label(
        self,
        api_client,
        user,
        member_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[member_label.pk])

        response = api_client.patch(
            url,
            {
                "name": "Enhancement",
            },
        )

        assert response.status_code == 200

        member_label.refresh_from_db()

        assert member_label.name == "Enhancement"

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_update_label_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[stranger_label.pk])

        response = api_client.patch(
            url,
            {
                "name": "Feature",
            },
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_invalid_color_returns_400(
        self,
        api_client,
        user,
        owner_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[owner_label.pk])

        response = api_client.patch(
            url,
            {
                "color": "",
            },
        )

        assert response.status_code == 400
        assert "color" in response.data

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_update_nonexistent_label_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[999999])

        response = api_client.patch(
            url,
            {
                "name": "Feature",
            },
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCardLabelDestroyView:
    """Tests for CardLabelViewSet.destroy()."""

    @pytest.fixture
    def owner_label(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardLabelFactory(
            card=card,
            name="Bug",
        )

    @pytest.fixture
    def member_label(self, user):
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

        return CardLabelFactory(
            card=card,
            name="Feature",
        )

    @pytest.fixture
    def stranger_label(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardLabelFactory(
            card=card,
            name="Bug",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_label(
        self,
        api_client,
        owner_label,
    ):
        url = reverse("cardlabel-detail", args=[owner_label.pk])

        response = api_client.delete(url)

        assert response.status_code == 401
        assert CardLabel.objects.filter(pk=owner_label.pk).exists()

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_delete_label(
        self,
        mock_log,
        api_client,
        user,
        owner_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[owner_label.pk])

        response = api_client.delete(url)

        assert response.status_code == 204
        assert not CardLabel.objects.filter(pk=owner_label.pk).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_label.card.board_list.board
        assert kwargs["board_list"] == owner_label.card.board_list
        assert kwargs["card"] == owner_label.card
        assert kwargs["action_type"] == "remove_card_label"
        assert kwargs["text"] == (
            f"The '{owner_label.name}' label in "
            f"'{owner_label.card.name}' card was removed"
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_delete_label(
        self,
        mock_log,
        api_client,
        user,
        member_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[member_label.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not CardLabel.objects.filter(pk=member_label.pk).exists()

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_user_cannot_delete_label_from_unrelated_board(
        self,
        mock_log,
        api_client,
        user,
        stranger_label,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[stranger_label.pk])

        response = api_client.delete(url)

        assert response.status_code == 404

        assert CardLabel.objects.filter(pk=stranger_label.pk).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_label_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardlabel-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End CardLabelViewSet Tests
#======================


#======================
#  Start BoardListViewSet Tests
#======================



@pytest.mark.django_db
class TestBoardListListView:
    """Tests for BoardListViewSet.list()."""

    @pytest.fixture
    def url(self):
        return reverse("boardlist-list")

    @pytest.fixture
    def owner_lists(self, user):
        board = BoardFactory(owner=user)

        return BoardListFactory.create_batch(
            3,
            board=board,
        )

    @pytest.fixture
    def member_lists(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        return BoardListFactory.create_batch(
            2,
            board=board,
        )

    @pytest.fixture
    def stranger_lists(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        return BoardListFactory.create_batch(
            4,
            board=board,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_list_board_lists(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_list_board_lists(
        self,
        api_client,
        user,
        url,
        owner_lists,
        stranger_lists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {board_list.id for board_list in owner_lists}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_list_board_lists(
        self,
        api_client,
        user,
        url,
        member_lists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        returned_ids = {item["id"] for item in response.data}
        expected_ids = {board_list.id for board_list in member_lists}

        assert returned_ids == expected_ids

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_board_lists_from_other_boards_are_not_returned(
        self,
        api_client,
        user,
        url,
        owner_lists,
        stranger_lists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        returned_ids = {item["id"] for item in response.data}
        stranger_ids = {board_list.id for board_list in stranger_lists}

        assert returned_ids.isdisjoint(stranger_ids)

    # ---------------------------------------------------------
    # Distinct
    # ---------------------------------------------------------

    def test_list_contains_no_duplicates(
        self,
        api_client,
        user,
        url,
        owner_lists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        ids = [item["id"] for item in response.data]

        assert len(ids) == len(set(ids))

    # ---------------------------------------------------------
    # Serializer
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        url,
        owner_lists,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data[0].keys()) == {
            "id", "order", "name", "cover_image", "cover_color", "list_cards", "archived","board"
        }



@pytest.mark.django_db
class TestBoardListRetrieveView:
    """Tests for BoardListViewSet.retrieve()."""

    @pytest.fixture
    def owner_board_list(self, user):
        board = BoardFactory(owner=user)
        board_list = BoardListFactory(board=board)

        CardFactory.create_batch(2, board_list=board_list)

        return board_list

    @pytest.fixture
    def member_board_list(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        board_list = BoardListFactory(board=board)

        CardFactory.create_batch(2, board_list=board_list)

        return board_list

    @pytest.fixture
    def stranger_board_list(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        board_list = BoardListFactory(board=board)

        CardFactory.create_batch(2, board_list=board_list)

        return board_list

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_retrieve_board_list(
        self,
        api_client,
        owner_board_list,
    ):
        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.get(url)

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    def test_board_owner_can_retrieve_board_list(
        self,
        api_client,
        user,
        owner_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == owner_board_list.id
        assert response.data["board"] == owner_board_list.board.id
        assert response.data["name"] == owner_board_list.name
        assert response.data["order"] == owner_board_list.order
        assert response.data["cover_color"] == owner_board_list.cover_color
        assert response.data["cover_image"] == owner_board_list.cover_image
        assert response.data["archived"] == owner_board_list.archived
        assert len(response.data["list_cards"]) == 2

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    def test_board_member_can_retrieve_board_list(
        self,
        api_client,
        user,
        member_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[member_board_list.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == member_board_list.id
        assert response.data["board"] == member_board_list.board.id
        assert response.data["name"] == member_board_list.name

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_retrieve_board_list_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[stranger_board_list.pk])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_retrieve_nonexistent_board_list_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[999999])

        response = api_client.get(url)

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Serializer fields
    # ---------------------------------------------------------

    def test_response_contains_expected_fields(
        self,
        api_client,
        user,
        owner_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.get(url)

        assert response.status_code == 200

        assert set(response.data.keys()) == {
            "id",
            "order",
            "name",
            "cover_image",
            "cover_color",
            "list_cards",
            "archived",
            "board",
        }


@pytest.mark.django_db
class TestBoardListCreateView:
    """Tests for BoardListViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("boardlist-list")

    @pytest.fixture
    def owner_board(self, user):
        return BoardFactory(owner=user)

    @pytest.fixture
    def member_board(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        return board

    @pytest.fixture
    def stranger_board(self):
        owner = UserFactory()
        return BoardFactory(owner=owner)

    @pytest.fixture
    def valid_data(self, owner_board):
        return {
            "board": owner_board.id,
            "name": "To Do",
            "order": 1,
            "cover_color": "#ffffff",
            "archived": False,
        }

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_board_list(
        self,
        api_client,
        url,
        valid_data,
    ):
        response = api_client.post(url, valid_data)

        assert response.status_code == 401
        assert BoardList.objects.count() == 0

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_create_board_list(
        self,
        mock_log,
        api_client,
        user,
        url,
        owner_board,
        valid_data,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(url, valid_data)

        assert response.status_code == 201

        board_list = BoardList.objects.get()

        assert board_list.board == owner_board
        assert board_list.name == valid_data["name"]
        assert board_list.order == valid_data["order"]
        assert board_list.cover_color == valid_data["cover_color"]
        assert board_list.archived is False

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_board
        assert kwargs["board_list"] == board_list
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "create_list"
        assert kwargs["text"] == f"'{board_list.name}' list added to board"

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_create_board_list(
        self,
        mock_log,
        api_client,
        user,
        url,
        member_board,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "board": member_board.id,
                "name": "Doing",
                "order": 2,
                "cover_color": "#00ff00",
                "archived": False,
            },
        )

        assert response.status_code == 201

        board_list = BoardList.objects.get()

        assert board_list.board == member_board
        assert board_list.name == "Doing"

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_user_cannot_create_board_list_for_unrelated_board(
        self,
        api_client,
        user,
        url,
        stranger_board,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "board": stranger_board.id,
                "name": "To Do",
                "order": 1,
            },
        )

        assert response.status_code == 403
        assert BoardList.objects.count() == 0

    def test_missing_board_returns_400(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "name": "To Do",
                "order": 1,
            },
        )

        assert response.status_code == 400
        assert BoardList.objects.count() == 0

    def test_invalid_board_returns_403(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.post(
            url,
            {
                "board": 999999,
                "name": "To Do",
                "order": 1,
            },
        )

        assert response.status_code == 403
        assert BoardList.objects.count() == 0

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    @pytest.mark.parametrize("missing_field", ["name"])
    def test_required_fields(
        self,
        api_client,
        user,
        url,
        valid_data,
        missing_field,
    ):
        api_client.force_authenticate(user)

        data = valid_data.copy()
        data.pop(missing_field)

        response = api_client.post(url, data)

        assert response.status_code == 400
        assert missing_field in response.data

        assert BoardList.objects.count() == 0


@pytest.mark.django_db
class TestBoardListUpdateView:
    """Tests for BoardListViewSet.update()."""

    @pytest.fixture
    def owner_board_list(self, user):
        board = BoardFactory(owner=user)
        return BoardListFactory(
            board=board,
            name="To Do",
            order=1,
        )

    @pytest.fixture
    def member_board_list(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        return BoardListFactory(
            board=board,
            name="To Do",
            order=1,
        )

    @pytest.fixture
    def stranger_board_list(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        return BoardListFactory(
            board=board,
            name="To Do",
            order=1,
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_update_board_list(
        self,
        api_client,
        owner_board_list,
    ):
        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.patch(
            url,
            {"name": "Done"},
        )

        assert response.status_code == 401

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_update_name(
        self,
        mock_log,
        api_client,
        user,
        owner_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.patch(
            url,
            {"name": "Done"},
        )

        assert response.status_code == 200

        owner_board_list.refresh_from_db()

        assert owner_board_list.name == "Done"

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_board_list.board
        assert kwargs["board_list"] == owner_board_list
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "edit_list_title"
        assert kwargs["text"] == (
            "The name of the list was changed "
            "from 'To Do' to 'Done' "
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_update_name(
        self,
        mock_log,
        api_client,
        user,
        member_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[member_board_list.pk])

        response = api_client.patch(
            url,
            {"name": "In Progress"},
        )

        assert response.status_code == 200

        member_board_list.refresh_from_db()

        assert member_board_list.name == "In Progress"

        mock_log.assert_called_once()

    # ---------------------------------------------------------
    # No activity
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_update_without_name_change_does_not_create_activity(
        self,
        mock_log,
        api_client,
        user,
        owner_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.patch(
            url,
            {
                "order": 10,
            },
        )

        assert response.status_code == 200

        owner_board_list.refresh_from_db()

        assert owner_board_list.order == 10

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def test_invalid_name_returns_400(
        self,
        api_client,
        user,
        owner_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.patch(
            url,
            {"name": ""},
        )

        assert response.status_code == 400
        assert "name" in response.data

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    def test_user_cannot_update_board_list_from_unrelated_board(
        self,
        api_client,
        user,
        stranger_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[stranger_board_list.pk])

        response = api_client.patch(
            url,
            {"name": "Done"},
        )

        assert response.status_code == 404

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_update_nonexistent_board_list_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[999999])

        response = api_client.patch(
            url,
            {"name": "Done"},
        )

        assert response.status_code == 404



@pytest.mark.django_db
class TestBoardListDestroyView:
    """Tests for BoardListViewSet.destroy()."""

    @pytest.fixture
    def owner_board_list(self, user):
        board = BoardFactory(owner=user)

        return BoardListFactory(
            board=board,
            name="To Do",
        )

    @pytest.fixture
    def member_board_list(self, user):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        return BoardListFactory(
            board=board,
            name="Doing",
        )

    @pytest.fixture
    def stranger_board_list(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)

        return BoardListFactory(
            board=board,
            name="Done",
        )

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_board_list(
        self,
        api_client,
        owner_board_list,
    ):
        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.delete(url)

        assert response.status_code == 401
        assert BoardList.objects.filter(pk=owner_board_list.pk).exists()

    # ---------------------------------------------------------
    # Board owner
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_delete_board_list(
        self,
        mock_log,
        api_client,
        user,
        owner_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[owner_board_list.pk])

        response = api_client.delete(url)

        assert response.status_code == 204
        assert not BoardList.objects.filter(pk=owner_board_list.pk).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == owner_board_list.board
        assert kwargs["board_list"].name == owner_board_list.name
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "remove_list"
        assert kwargs["text"] == (
            f"The '{owner_board_list.name}' list was removed"
        )

    # ---------------------------------------------------------
    # Board member
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_member_can_delete_board_list(
        self,
        mock_log,
        api_client,
        user,
        member_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[member_board_list.pk])

        response = api_client.delete(url)

        assert response.status_code == 204
        assert not BoardList.objects.filter(pk=member_board_list.pk).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == user
        assert kwargs["user"] == user
        assert kwargs["board"] == member_board_list.board
        assert kwargs["board_list"].name == member_board_list.name
        assert kwargs["card"] is None
        assert kwargs["action_type"] == "remove_list"
        assert kwargs["text"] == (
            f"The '{member_board_list.name}' list was removed"
        )

    # ---------------------------------------------------------
    # Queryset filtering
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_user_cannot_delete_board_list_from_unrelated_board(
        self,
        mock_log,
        api_client,
        user,
        stranger_board_list,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[stranger_board_list.pk])

        response = api_client.delete(url)

        assert response.status_code == 404

        assert BoardList.objects.filter(
            pk=stranger_board_list.pk
        ).exists()

        mock_log.assert_not_called()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_board_list_returns_404(
        self,
        api_client,
        user,
    ):
        api_client.force_authenticate(user)

        url = reverse("boardlist-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End BoardListViewSet Tests
#======================


#======================
#  Start CardMemberViewSet Tests
#======================




@pytest.mark.django_db
class TestCardMemberListView:
    """Tests that CardMemberViewSet does not allow list()."""

    @pytest.fixture
    def url(self):
        return reverse("cardmember-list")

    def test_list_method_is_not_allowed_for_authenticated_user(
        self,
        api_client,
        user,
        url,
    ):
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 405

    def test_list_method_is_not_allowed_for_anonymous_user(
        self,
        api_client,
        url,
    ):
        response = api_client.get(url)

        assert response.status_code == 401


@pytest.mark.django_db
class TestCardMemberRetrieveView:
    """Tests that CardMemberViewSet does not allow retrieve()."""

    @pytest.fixture
    def membership(self):
        owner = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        member = UserFactory()

        return CardMembershipFactory(
            card=card,
            user=member,
        )

    def test_retrieve_method_is_not_allowed_for_authenticated_user(
        self,
        api_client,
        user,
        membership,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardmember-detail", args=[membership.pk])

        response = api_client.get(url)

        assert response.status_code == 405

    def test_retrieve_method_is_not_allowed_for_anonymous_user(
        self,
        api_client,
        membership,
    ):
        url = reverse("cardmember-detail", args=[membership.pk])

        response = api_client.get(url)

        assert response.status_code == 401


@pytest.mark.django_db
class TestCardMemberCreateView:
    """Tests for CardMemberViewSet.create()."""

    @pytest.fixture
    def url(self):
        return reverse("cardmember-list")

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
    def card(self, board_list):
        return CardFactory(board_list=board_list)

    @pytest.fixture
    def board_member(self, board):
        user = UserFactory()

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        return user

    @pytest.fixture
    def pending_member(self, board):
        user = UserFactory()

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=False,
        )

        return user

    @pytest.fixture
    def outsider(self):
        return UserFactory()

    @pytest.fixture
    def valid_data(self, card, board_member):
        return {
            "card": card.id,
            "user": board_member.id,
        }

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_create_card_membership(
        self,
        api_client,
        url,
        valid_data,
    ):
        response = api_client.post(url, valid_data)

        assert response.status_code == 401
        assert CardMembership.objects.count() == 0

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_add_board_member_to_card(
        self,
        mock_log,
        api_client,
        owner,
        card,
        board_member,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "user": board_member.id,
            },
        )

        assert response.status_code == 201

        membership = CardMembership.objects.get()

        assert membership.card == card
        assert membership.user == board_member

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["user"] == owner
        assert kwargs["board"] == card.board_list.board
        assert kwargs["board_list"] == card.board_list
        assert kwargs["card"] == card
        assert kwargs["action_type"] == "add_card_member"

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    def test_board_member_cannot_add_card_member(
        self,
        api_client,
        board_member,
        card,
        outsider,
        url,
    ):
        api_client.force_authenticate(board_member)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "user": outsider.id,
            },
        )

        assert response.status_code == 403
        assert CardMembership.objects.count() == 0

    def test_cannot_add_user_who_is_not_board_member(
        self,
        api_client,
        owner,
        card,
        outsider,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "user": outsider.id,
            },
        )

        assert response.status_code == 403
        assert CardMembership.objects.count() == 0

    def test_cannot_add_pending_board_member(
        self,
        api_client,
        owner,
        card,
        pending_member,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "user": pending_member.id,
            },
        )

        assert response.status_code == 403
        assert CardMembership.objects.count() == 0

    def test_missing_card_returns_403(
        self,
        api_client,
        owner,
        board_member,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "user": board_member.id,
            },
        )

        assert response.status_code == 403
        assert CardMembership.objects.count() == 0

    def test_invalid_card_returns_403(
        self,
        api_client,
        owner,
        board_member,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "card": 999999,
                "user": board_member.id,
            },
        )

        assert response.status_code == 403
        assert CardMembership.objects.count() == 0

    # ---------------------------------------------------------
    # Serializer validation
    # ---------------------------------------------------------

    def test_missing_user_returns_403(
        self,
        api_client,
        owner,
        card,
        url,
    ):
        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "card": card.id,
            },
        )

        assert response.status_code == 403


    def test_duplicate_card_membership_returns_400(
        self,
        api_client,
        owner,
        card,
        board_member,
        url,
    ):
        CardMembership.objects.create(
            card=card,
            user=board_member,
        )

        api_client.force_authenticate(owner)

        response = api_client.post(
            url,
            {
                "card": card.id,
                "user": board_member.id,
            },
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestCardMemberUpdateView:
    """Tests that CardMemberViewSet does not allow updates."""

    @pytest.fixture
    def membership(self):
        owner = UserFactory()
        member = UserFactory()

        board = BoardFactory(owner=owner)
        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        return CardMembershipFactory(
            card=card,
            user=member,
        )

    def test_put_method_is_not_allowed(
        self,
        api_client,
        user,
        membership,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardmember-detail", args=[membership.pk])

        response = api_client.put(
            url,
            {
                "card": membership.card.id,
                "user": membership.user.id,
            },
        )

        assert response.status_code == 405

    def test_patch_method_is_not_allowed(
        self,
        api_client,
        user,
        membership,
    ):
        api_client.force_authenticate(user)

        url = reverse("cardmember-detail", args=[membership.pk])

        response = api_client.patch(
            url,
            {
                "user": membership.user.id,
            },
        )

        assert response.status_code == 405


@pytest.mark.django_db
class TestCardMemberDestroyView:
    """Tests for CardMemberViewSet.destroy()."""

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
    def card(self, board_list):
        return CardFactory(board_list=board_list)

    @pytest.fixture
    def member(self, board):
        user = UserFactory()

        BoardMembership.objects.create(
            board=board,
            user=user,
            member_type="member",
            accepted=True,
        )

        return user

    @pytest.fixture
    def card_membership(self, card, member):
        return CardMembershipFactory(
            card=card,
            user=member,
        )

    @pytest.fixture
    def outsider(self):
        return UserFactory()

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------

    def test_anonymous_user_cannot_delete_card_membership(
        self,
        api_client,
        card_membership,
    ):
        url = reverse("cardmember-detail", args=[card_membership.pk])

        response = api_client.delete(url)

        assert response.status_code == 401

        assert CardMembership.objects.filter(
            pk=card_membership.pk
        ).exists()

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    @patch("api.board.views.ActivityLog.log")
    def test_board_owner_can_delete_card_membership(
        self,
        mock_log,
        api_client,
        owner,
        card_membership,
    ):
        api_client.force_authenticate(owner)

        url = reverse("cardmember-detail", args=[card_membership.pk])

        response = api_client.delete(url)

        assert response.status_code == 204

        assert not CardMembership.objects.filter(
            pk=card_membership.pk
        ).exists()

        mock_log.assert_called_once()

        kwargs = mock_log.call_args.kwargs

        assert kwargs["request"].user == owner
        assert kwargs["user"] == owner
        assert kwargs["board"] == card_membership.card.board_list.board
        assert kwargs["card"] == card_membership.card
        assert kwargs["action_type"] == "remove_card_member"
        assert (
            kwargs["text"]
            == f"The '{card_membership.user.username}' removed from '{card_membership.card.name}' card"
        )

    # ---------------------------------------------------------
    # Object permission
    # ---------------------------------------------------------

    def test_board_member_cannot_delete_card_membership(
        self,
        api_client,
        member,
        card_membership,
    ):
        api_client.force_authenticate(member)

        url = reverse("cardmember-detail", args=[card_membership.pk])

        response = api_client.delete(url)

        assert response.status_code == 404

        assert CardMembership.objects.filter(
            pk=card_membership.pk
        ).exists()

    def test_unrelated_user_cannot_delete_card_membership(
        self,
        api_client,
        outsider,
        card_membership,
    ):
        api_client.force_authenticate(outsider)

        url = reverse("cardmember-detail", args=[card_membership.pk])

        response = api_client.delete(url)

        assert response.status_code == 404

        assert CardMembership.objects.filter(
            pk=card_membership.pk
        ).exists()

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    def test_delete_nonexistent_card_membership_returns_404(
        self,
        api_client,
        owner,
    ):
        api_client.force_authenticate(owner)

        url = reverse("cardmember-detail", args=[999999])

        response = api_client.delete(url)

        assert response.status_code == 404
#======================
#  End CardMemberViewSet Tests
#======================