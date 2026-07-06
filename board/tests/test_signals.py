import pytest

from board.models import CardMembership

from api.tests.conftest import (
    UserFactory,
    BoardFactory,
    BoardMembershipFactory,
    BoardListFactory,
    CardFactory,
    CardMembershipFactory,
)


@pytest.mark.django_db
class TestDeleteCardMembershipSignal:

    @pytest.fixture
    def user(self):
        return UserFactory()

    @pytest.fixture
    def other_user(self):
        return UserFactory()

    @pytest.fixture
    def board(self):
        return BoardFactory()

    @pytest.fixture
    def other_board(self):
        return BoardFactory()

    # ------------------------------------------------------------------
    # Success
    # ------------------------------------------------------------------

    def test_deleting_board_membership_removes_card_memberships(
        self,
        user,
        board,
    ):
        board_membership = BoardMembershipFactory(
            board=board,
            user=user,
        )

        board_list = BoardListFactory(board=board)

        card1 = CardFactory(board_list=board_list)
        card2 = CardFactory(board_list=board_list)

        card_membership1 = CardMembershipFactory(
            user=user,
            card=card1,
        )

        card_membership2 = CardMembershipFactory(
            user=user,
            card=card2,
        )

        board_membership.delete()

        assert not CardMembership.objects.filter(
            pk=card_membership1.pk,
        ).exists()

        assert not CardMembership.objects.filter(
            pk=card_membership2.pk,
        ).exists()

    # ------------------------------------------------------------------
    # Other board
    # ------------------------------------------------------------------

    def test_card_memberships_on_other_boards_are_not_deleted(
        self,
        user,
        board,
        other_board,
    ):
        board_membership = BoardMembershipFactory(
            board=board,
            user=user,
        )

        list1 = BoardListFactory(board=board)
        list2 = BoardListFactory(board=other_board)

        card1 = CardFactory(board_list=list1)
        card2 = CardFactory(board_list=list2)

        membership1 = CardMembershipFactory(
            user=user,
            card=card1,
        )

        membership2 = CardMembershipFactory(
            user=user,
            card=card2,
        )

        board_membership.delete()

        assert not CardMembership.objects.filter(
            pk=membership1.pk,
        ).exists()

        assert CardMembership.objects.filter(
            pk=membership2.pk,
        ).exists()

    # ------------------------------------------------------------------
    # Other user
    # ------------------------------------------------------------------

    def test_other_users_card_memberships_are_not_deleted(
        self,
        user,
        other_user,
        board,
    ):
        board_membership = BoardMembershipFactory(
            board=board,
            user=user,
        )

        board_list = BoardListFactory(board=board)
        card = CardFactory(board_list=board_list)

        own_membership = CardMembershipFactory(
            user=user,
            card=card,
        )

        other_membership = CardMembershipFactory(
            user=other_user,
            card=card,
        )

        board_membership.delete()

        assert not CardMembership.objects.filter(
            pk=own_membership.pk,
        ).exists()

        assert CardMembership.objects.filter(
            pk=other_membership.pk,
        ).exists()

    # ------------------------------------------------------------------
    # No card memberships
    # ------------------------------------------------------------------

    def test_delete_board_membership_without_card_memberships(
        self,
        user,
        board,
    ):
        board_membership = BoardMembershipFactory(
            board=board,
            user=user,
        )

        board_membership.delete()

        assert CardMembership.objects.count() == 0