from django.contrib import admin
from .models import Board, BoardMembership, BoardList, Card, CardLabel, CheckList, ChecklistItem

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
	list_display = ["user", "name"]


@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
	list_display = ["user", "board", "member_type", "created"]


@admin.register(BoardList)
class BoardListAdmin(admin.ModelAdmin):
	list_display = ["order", "board", "name", "created"]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
	list_display = ["name", "board_list", "created"]

@admin.register(CardLabel)
class CardLabelAdmin(admin.ModelAdmin):
	list_display = ["name", "card", "label", "created"]

@admin.register(CheckList)
class CheckListAdmin(admin.ModelAdmin):
	list_display = ["name", "card", "created"]

@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
	list_display = ["name", "checklist", "is_completed", "created"]