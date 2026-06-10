from django.contrib import admin
from .models import (
	Board, BoardMembership, BoardList, 
	Card, CardLabel, CheckList, ChecklistItem, 
	CardFile, CardImage, Comment,
	CardWatch, BoardWatch,CardMembership,LinkAttachment,
	Activity
	)

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
	list_display = ["owner", "name", "id"]


@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
	list_display = ["user", "board", "member_type", "created"]


@admin.register(BoardList)
class BoardListAdmin(admin.ModelAdmin):
	list_display = ["order", "board", "name", "created"]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
	list_display = ["name", "board_list", "order", "created"]

@admin.register(CardLabel)
class CardLabelAdmin(admin.ModelAdmin):
	list_display = ["name", "card", "color", "created"]

@admin.register(CheckList)
class CheckListAdmin(admin.ModelAdmin):
	list_display = ["name", "card", "created"]

@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
	list_display = ["name", "checklist", "is_completed", "created"]



@admin.register(CardFile)
class FileAttachmentAdmin(admin.ModelAdmin):
	list_display = ["name", "user", "card"]

@admin.register(CardImage)
class ImageAttachmentAdmin(admin.ModelAdmin):
	list_display = ["name", "user", "card"]

@admin.register(LinkAttachment)
class ImageAttachmentAdmin(admin.ModelAdmin):
	list_display = ["name", "user", "card"]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ["user", "card", "content"]


@admin.register(CardWatch)
class CardWatchAdmin(admin.ModelAdmin):
	list_display = ["user", "card", "watch"]

@admin.register(BoardWatch)
class BoardWatchAdmin(admin.ModelAdmin):
	list_display = ["user", "board", "watch"]


@admin.register(CardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
	list_display = ["user", "card", "created"]



@admin.register(Activity)
class BoardMembershipAdmin(admin.ModelAdmin):
	list_display = ["user", "board", "board_list", "card", "action_type", "text", "created"]