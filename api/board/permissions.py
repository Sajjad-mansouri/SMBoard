from rest_framework import permissions
from board import models

class IsBoardOwner(permissions.BasePermission):

	def has_object_permission(self, request, view, obj):

		return obj.owner == request.user


class IsBoardOwnerOrMember(permissions.BasePermission):

	def has_object_permission(self, request, view, obj):
		if isinstance(obj, models.Board):
			return obj.owner == request.user | obj.board_memberships.filter(user=request.user).exists()

		elif isinstance(obj, models.BoardList):
			return (obj.board.owner == request.user) | obj.board.board_memberships.filter(user=request.user).exists()
		elif isinstance(obj, models.Card) | isinstance(obj, models.BoardWatch):
			return (obj.board_list.board.owner == request.user) | obj.card_memberships.filter(user=request.user).exists()

		elif isinstance(obj, models.ChecklistItem):
			return (obj.checklist.card.board_list.board.owner == request.user) | obj.checklist.card.card_memberships.filter(user=request.user).exists()
		elif (
			isinstance(obj, models.CardLabel)|
			isinstance(obj, models.CheckList)|
			isinstance(obj, models.CardFile) | 
			isinstance(obj,models.CardImage)| 
			isinstance(obj,models.Comment) |
			isinstance(obj,models.CardWatch)
			):
			return (obj.card.board_list.board.owner == request.user) | obj.card.card_memberships.filter(user=request.user).exists()



