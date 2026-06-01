from rest_framework import permissions
from django.db.models import Q
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




class CardMembershipPermission(permissions.BasePermission):
	"""
	Allow create based on the data being submitted
	"""
	def has_object_permission(self, request, view, obj):
		return (obj.card.board_list.board.owner == request.user)

	def has_permission(self, request, view):
		print(request.data)

		obj_id = request.data.get("card")
		user_id = request.data.get("user")
		if obj_id and user_id:
			q = Q(id=obj_id) & Q(board_list__board__owner=request.user) & Q(board_list__board__board_memberships__user_id=user_id)
			return models.Card.objects.filter(q).exists()
		else:
			return True