from django.apps import AppConfig




class BoardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'board'

    def ready(self):
        from . import signals
        from django.db.models.signals import post_delete
        from .models import BoardMembership
        post_delete.connect(signals.delete_card_membership, sender=BoardMembership, dispatch_uid="my_unique_identifier")