from rest_framework import viewsets, mixins
from board.models import Board
from . import serializers

class CreateListBoardViewSet(mixins.CreateModelMixin,
								mixins.ListModelMixin,
								mixins.RetrieveModelMixin,
								viewsets.GenericViewSet):

	serializer_class = serializers.BoardSerializer
	queryset = Board.objects.all()