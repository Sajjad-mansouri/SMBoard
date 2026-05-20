from rest_framework import viewsets, mixins
from board.models import Board
from . import serializers
from .permissions import IsBoardOwner

class CreateListBoardViewSet(mixins.CreateModelMixin,
								mixins.ListModelMixin,
								mixins.RetrieveModelMixin,
								viewsets.GenericViewSet):

	serializer_class = serializers.BoardSerializer
	permission_classes = [IsBoardOwner]

	def get_queryset(self):

		return Board.objects.filter(user=self.request.user)