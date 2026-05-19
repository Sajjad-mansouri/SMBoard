from django.contrib import admin
from .models import Board, BoardMembership

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
	list_display = ["user", "name"]


@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
	list_display = ["user", "board", "member_type", "created"]
