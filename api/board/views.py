from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins, views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, get_object_or_404, GenericAPIView, CreateAPIView
from board.models import (
	Board, Card, CheckList, 
	ChecklistItem, Comment, 
	CardFile, CardImage, 
	CardLabel, BoardList, 
	CardMembership,BoardMembership,
	BoardWatch, LinkAttachment,
	Activity
	)
from . import serializers
from rest_framework.permissions import AllowAny
from .permissions import IsBoardOwner, IsBoardOwnerOrMember, CardMembershipPermission, BoardMembershipPermission


UserModel = get_user_model()
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

class CardViewSet(viewsets.ModelViewSet):
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


class CardOrderUpdating(views.APIView):
	permission_classes = [IsBoardOwnerOrMember]
	def patch(self, request, *args, **kwargs):

		ids = [item["id"] for item in request.data]

		queryset = Card.objects.filter(id__in=ids)

		serializer = serializers.CardOrderSerializer(
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


class CardMemberViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardMembershipSerializer
	permission_classes = [CardMembershipPermission]
	http_method_names = ['delete', 'post']
	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user)
		return CardMembership.objects.filter(q).distinct()


class BoardMemberViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.BoardMembershipSerializer
	permission_classes = [BoardMembershipPermission]
	def get_queryset(self):

		q = Q(board__owner=self.request.user)
		return BoardMembership.objects.filter(q)

	def create(self, request, *args, **kwargs):
		search = request.data.get("search")
		if not search:
			return Response({"error": "Search parameter is required"},status=status.HTTP_400_BAD_REQUEST)

		user = get_object_or_404(UserModel, username=search)

		data = {
		"board": request.data.get("board"),
		"user_id":user.id,
		"accepted":True

		}
		serializer = self.get_serializer(data=data)
		if serializer.is_valid(raise_exception=False):
			self.perform_create(serializer)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		else:
			return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


class ToggleWatchMixin:
	def post(self, request, *args, **kwargs):
		
		serializer = self.serializer_class(
			data=request.data,
			context={"request":request}
			)
		if serializer.is_valid():
			serializer.save()
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		return Response(serializer.data, status=status.HTTP_200_OK)

class BoardWatchView(ToggleWatchMixin, views.APIView):
	serializer_class = serializers.BoardWatchSerializer

class CardWatchView(ToggleWatchMixin, views.APIView):
	serializer_class = serializers.CardWatchSerializer


class LinkAttachmentViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.LinkAttachmentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__card_memberships__user=self.request.user)
		return LinkAttachment.objects.filter(q).distinct()


class CopyCardView(GenericAPIView):
	serializer_class = serializers.CardNestedSerializer
	def post(self, request, *args, **kwargs):
		instance = self.get_object()
		instance.pk = None
		instance.order = None
		instance._state.adding = True
		instance.save()
		serializer = self.get_serializer(instance)
		return Response(serializer.data)

	def get_queryset(self):
		return Card.objects.all()



class ActivitytViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.ActivitySerializer
	permission_classes = [AllowAny]

	def get_queryset(self):

		return Activity.objects.all()