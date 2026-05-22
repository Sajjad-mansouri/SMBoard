from django.db.models import Q
from rest_framework import viewsets, mixins
from rest_framework.generics import ListAPIView, RetrieveAPIView
from board.models import Board, Card
from . import serializers
from .permissions import IsBoardOwner

class CreateListBoardViewSet(mixins.CreateModelMixin,
								mixins.ListModelMixin,
								mixins.RetrieveModelMixin,
								viewsets.GenericViewSet):

	serializer_class = serializers.BoardSerializer
	permission_classes = [IsBoardOwner]

	def get_queryset(self):

		return Board.objects.filter(owner=self.request.user)


class GuestBoardListView(ListAPIView):
	serializer_class = serializers.BoardSerializer
	def get_queryset(self):
		q = Q(board_memberships__user=self.request.user) & ~Q(owner=self.request.user)
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