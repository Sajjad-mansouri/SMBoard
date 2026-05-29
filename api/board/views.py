from django.db.models import Q
from rest_framework import viewsets, mixins, views
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from board.models import Board, Card, CheckList, ChecklistItem, Comment
from . import serializers
from .permissions import IsBoardOwner, IsBoardOwnerOrMember

class BoardViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.BoardSerializer
	permission_classes = [IsBoardOwner]

	def get_queryset(self):

		return Board.objects.filter(owner=self.request.user)


class GuestBoardListView(ListAPIView):
	serializer_class = serializers.BoardSerializer
	def get_queryset(self):
		q = Q(board_memberships__user=self.request.user) & ~Q(owner=self.request.user) & Q(closed=False)
		return Board.objects.filter(q)


class UserRetrieveView(RetrieveAPIView):
	serializer_class = serializers.UserSerializer

	def get_object(self):
		return self.request.user


class SearchBoardView(ListAPIView):
	serializer_class = serializers.BoardSerializer
	def get_queryset(self):
		search = self.request.query_params["search"]
		q = Q(board_memberships__user=self.request.user) | Q(owner=self.request.user)
		q = q & Q(name__icontains=search)
		return Board.objects.filter(q)


class SearchCardView(ListAPIView):
	serializer_class = serializers.CardSerializer
	def get_queryset(self):
		search = self.request.query_params["search"]

		q = Q(board_list__board__board_memberships__user=self.request.user) | Q(board_list__board__owner=self.request.user)
		q = q & Q(name__icontains=search)
		return Card.objects.filter(q)


class ClosedBoardView(ListAPIView):
	serializer_class = serializers.BoardSerializer
	def get_queryset(self):


		q = Q(owner=self.request.user)
		q = q & Q(closed=True)
		return Board.objects.filter(q)



class BoardRetrieveView(RetrieveAPIView):
	serializer_class = serializers.BoardNestedSerializer

	def get_queryset(self):
		q = (Q(board_memberships__user=self.request.user) | Q(owner=self.request.user)) & Q(closed=False)

		return Board.objects.filter(q).distinct()



class CardUpdateView(UpdateAPIView):
	serializer_class = serializers.CardNestedSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		return Card.objects.all()


class ChecklistViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CheckListSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):
		print(self.request.user)
		print(CheckList.objects.filter(card__board_list__board__owner=self.request.user))
		q = Q(card__board_list__board__owner=self.request.user) | Q(card__card_memberships__user=self.request.user)
		print(CheckList.objects.filter(q)[0].id)
		return CheckList.objects.filter(q)


class ChecklistItemViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CheckListItemSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(checklist__card__board_list__board__owner=self.request.user) | Q(checklist__card__card_memberships__user=self.request.user)
		print(ChecklistItem.objects.filter(q)[0].id)
		return ChecklistItem.objects.filter(q)


class CommentViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardCommentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def create(self, request, *args, **kwargs):
		# Debug: Try to create manually to see errors
		serializer = self.get_serializer(data=request.data)
		
		if not serializer.is_valid():
			print(f"Validation errors: {serializer.errors}")
			# Return actual errors instead of default 400
			return Response({
				'detail': serializer.errors,
				'received_data': request.data
			}, status=400)
		
		return super().create(request, *args, **kwargs)

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__card_memberships__user=self.request.user)
		print(Comment.objects.filter(q)[0].id)
		return Comment.objects.filter(q)

class CurrentUser(views.APIView):
	def get(self, request, format=None):
			"""
			Return a list of all users.
			"""
			
			return Response({"user":request.user.id})