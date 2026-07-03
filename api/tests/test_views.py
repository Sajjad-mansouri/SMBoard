import pytest
from django.urls import reverse
from unittest.mock import call, patch
from .conftest import BoardFactory
from board.models import Board


#======================
#  BoardViewSet Tests
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