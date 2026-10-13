from .models import BoardMembership, CardMembership


def delete_card_membership(sender, instance, **kwargs):
    user = instance.user
    board = instance.board
    CardMembership.objects.filter(user=user, card__board_list__board=board).delete()


def add_owner_membership(sender, instance, created, **kwargs):
    if created:
        BoardMembership.objects.create(
            board=instance, user=instance.owner, member_type="admin", accepted=True
        )
