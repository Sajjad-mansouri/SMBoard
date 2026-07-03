from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS
from django.db.models import Q
from board import models

class IsBoardOwner(permissions.BasePermission):

	def has_object_permission(self, request, view, obj):

		return obj.owner == request.user

	def has_permission(self, request, view):
		return bool(request.user and request.user.is_authenticated)



class IsBoardOwnerOrMember(permissions.BasePermission):

	def has_permission(self, request, view):
		print(request.data)
		print(view.action)
		if view.action == "create":
			if not request.user or not request.user.is_authenticated:
				return False
			if request.data.get("checklist"):
				q = Q(id=request.data.get("checklist")) & (Q(card__board_list__board__owner=request.user)| Q(card__board_list__board__board_memberships__user=request.user))
				return models.CheckList.objects.filter(q).exists()
			elif request.data.get("card"):

				q = Q(id=request.data.get("card")) & (Q(board_list__board__owner=request.user)| Q(board_list__board__board_memberships__user=request.user))
				return models.Card.objects.filter(q).exists()
			elif request.data.get("board_list"):

				q = Q(id=request.data.get("board_list")) & (Q(board__owner=request.user)| Q(board__board_memberships__user=request.user))
				return models.BoardList.objects.filter(q).exists()
			elif request.data.get("board"):

				q = Q(id=request.data.get("board")) & (Q(owner=request.user)| Q(board_memberships__user=request.user))
				return models.Board.objects.filter(q).exists()
		return bool(request.user and request.user.is_authenticated)
			


class CardMembershipPermission(permissions.BasePermission):
	"""
	Allow create based on the data being submitted
	"""
	def has_object_permission(self, request, view, obj):
		return (obj.card.board_list.board.owner == request.user)

	def has_permission(self, request, view):

		if view.action == "create":

			obj_id = request.data.get("card")
			user_id = request.data.get("user")
			q = Q(id=obj_id) & Q(board_list__board__owner=request.user) & Q(board_list__board__board_memberships__user_id=user_id)
			return models.Card.objects.filter(q).exists()

		else:
			return bool(request.user and request.user.is_authenticated)


class BoardMembershipPermission(permissions.BasePermission):
	"""
	Allow create based on the data being submitted
	"""
	def has_object_permission(self, request, view, obj):

		return (obj.board.owner == request.user)

	def has_permission(self, request, view):


		if view.action == "create":
			obj_id = request.data.get("board")

			q = Q(id=obj_id)& Q(owner=request.user)
			return models.Board.objects.filter(q).exists()

		else:
			return bool(request.user and request.user.is_authenticated)



class WatchBoardCardPermission(permissions.BasePermission):
	def has_permission(self, request, view):
		board = request.data.get("board")
		card = request.data.get("card")

		if board:
			q = Q(id=board) & (Q(owner=request.user)| Q(board_memberships__user=request.user))
			return models.Board.objects.filter(q).exists()
		elif card:
			q = Q(id=card) & (Q(board_list__board__owner=request.user)| Q(board_list__board__board_memberships__user=request.user))
			return models.Card.objects.filter(q).exists()