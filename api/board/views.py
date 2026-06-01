from django.db.models import Q
from rest_framework import viewsets, mixins, views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from board.models import Board, Card, CheckList, ChecklistItem, Comment, CardFile, CardImage, CardLabel, BoardList
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
		return Board.objects.filter(q).distinct()


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
		return Board.objects.filter(q).distinct()


class SearchCardView(ListAPIView):
	serializer_class = serializers.CardSerializer
	def get_queryset(self):
		search = self.request.query_params["search"]

		q = Q(board_list__board__board_memberships__user=self.request.user) | Q(board_list__board__owner=self.request.user)
		q = q & Q(name__icontains=search)
		return Card.objects.filter(q).distinct()


class ClosedBoardView(ListAPIView):
	serializer_class = serializers.BoardSerializer
	def get_queryset(self):


		q = Q(owner=self.request.user)
		q = q & Q(closed=True)
		return Board.objects.filter(q).distinct()



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
		return CheckList.objects.filter(q).distinct()


class ChecklistItemViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CheckListItemSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(checklist__card__board_list__board__owner=self.request.user) | Q(checklist__card__card_memberships__user=self.request.user)
		print(ChecklistItem.objects.filter(q)[0].id)
		return ChecklistItem.objects.filter(q).distinct()


class CommentViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardCommentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__card_memberships__user=self.request.user)
		print(Comment.objects.filter(q)[0].id)
		return Comment.objects.filter(q).distinct()

class CurrentUser(views.APIView):
	def get(self, request, format=None):
			"""
			Return a list of all users.
			"""
			
			return Response({"user":request.user.id})


class CardFileViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.FileAttachmentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__card_memberships__user=self.request.user)

		return CardFile.objects.filter(q).distinct()

class CardImageViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.ImageAttachmentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__card_memberships__user=self.request.user)
		return CardImage.objects.filter(q).distinct()


class CardLabelViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardLabelSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__card_memberships__user=self.request.user)
		return CardLabel.objects.filter(q).distinct()

class BoardListViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.BoardListSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(board__owner=self.request.user) | Q(board__board_memberships__user=self.request.user)
		return BoardList.objects.filter(q).distinct()


class BoardListOrderUpdating(views.APIView):
	permission_classes = [IsBoardOwnerOrMember]
	def patch(self, request, *args, **kwargs):
		ids = [item["id"] for item in request.data]

		queryset = BoardList.objects.filter(id__in=ids)

		serializer = serializers.BoardListOrderSerializer(
			queryset,
			data=request.data,
			many=True,
			partial=True,
			context={"request":request}
			)

		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)