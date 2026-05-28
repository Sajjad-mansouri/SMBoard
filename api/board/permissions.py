from rest_framework import permissions

class IsBoardOwner(permissions.BasePermission):

	def has_object_permission(self, request, view, obj):

		return obj.owner == request.user


class IsBoardOwnerOrMemberOfCard(permissions.BasePermission):

	def has_object_permission(self, request, view, obj):

		return (obj.board_list.board.owner == request.user) | obj.card_memberships.filter(user=request.user).exists()