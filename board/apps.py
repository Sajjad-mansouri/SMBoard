from django.apps import AppConfig




class BoardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'board'

    def ready(self):
        from . import signals
        from django.db.models.signals import post_delete, post_save
        from .models import BoardMembership, Board
        post_delete.connect(signals.delete_card_membership, sender=BoardMembership, dispatch_uid="my_unique_identifier")
        post_save.connect(signals.add_owner_membership, sender=Board, dispatch_uid="add_owner_membership")
