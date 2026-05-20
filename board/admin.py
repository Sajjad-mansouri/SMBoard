from django.contrib import admin
from .models import Board, BoardMembership, BoardList

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
	list_display = ["user", "name"]


@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
	list_display = ["user", "board", "member_type", "created"]


@admin.register(BoardList)
class BoardListAdmin(admin.ModelAdmin):
	list_display = ["order", "board", "name", "created"]
