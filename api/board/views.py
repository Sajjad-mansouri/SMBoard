from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
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
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsBoardOwner, IsBoardOwnerOrMember, CardMembershipPermission, BoardMembershipPermission, WatchBoardCardPermission


UserModel = get_user_model()
class BoardViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.BoardSerializer
	permission_classes = [IsBoardOwner]

	def get_queryset(self):

		return Board.objects.filter(owner=self.request.user)


class GuestBoardListView(ListAPIView):
	serializer_class = serializers.BoardSerializer
	permission_classes = [IsAuthenticated]
	def get_queryset(self):
		q = Q(board_memberships__user=self.request.user) & ~Q(owner=self.request.user) & Q(closed=False)
		return Board.objects.filter(q).distinct()


class UserRetrieveView(RetrieveAPIView):
	serializer_class = serializers.UserSerializer
	permission_classes = [IsAuthenticated]
	def get_object(self):
		return self.request.user


class SearchBoardView(ListAPIView):
	serializer_class = serializers.BoardSerializer
	permission_classes = [IsAuthenticated]
	def get_queryset(self):
		search = self.request.query_params["search"]
		q = Q(board_memberships__user=self.request.user) | Q(owner=self.request.user)
		q = q & Q(name__icontains=search)
		return Board.objects.filter(q).distinct()


class SearchCardView(ListAPIView):
	serializer_class = serializers.CardSerializer
	permission_classes = [IsAuthenticated]
	def get_queryset(self):
		search = self.request.query_params["search"]

		q = Q(board_list__board__board_memberships__user=self.request.user) | Q(board_list__board__owner=self.request.user)
		q = q & Q(name__icontains=search)
		return Card.objects.filter(q).distinct()


class ClosedBoardView(ListAPIView):
	serializer_class = serializers.BoardSerializer
	permission_classes = [IsAuthenticated]
	def get_queryset(self):


		q = Q(owner=self.request.user)
		q = q & Q(closed=True)
		return Board.objects.filter(q).distinct()



class BoardRetrieveView(RetrieveAPIView):
	serializer_class = serializers.BoardNestedSerializer

	def get_queryset(self):
		q = (Q(board_memberships__user=self.request.user) | Q(owner=self.request.user)) & Q(closed=False)

		return Board.objects.filter(q).distinct()



class CardViewSet(viewsets.ModelViewSet):
	serializer_class = serializers.CardNestedSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):
		card__board_list__board__board_memberships__user=self.request.user
		q = Q(board_list__board__owner=self.request.user) | Q(board_list__board__board_memberships__user=self.request.user)

		return Card.objects.filter(q)

class CardArchivedUpdateView(UpdateAPIView):
	serializer_class = serializers.CardArchivedSerializer

	def get_queryset(self):

		q = Q(board_list__board__owner=self.request.user)

		return Card.objects.filter(q)

class ChecklistViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CheckListSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):
		
		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		
		return CheckList.objects.filter(q).distinct()


class ChecklistItemViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CheckListItemSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(checklist__card__board_list__board__owner=self.request.user) | Q(checklist__card__board_list__board__board_memberships__user=self.request.user)
		
		return ChecklistItem.objects.filter(q).distinct()


class CommentViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardCommentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		
		return Comment.objects.filter(q).distinct()

class CurrentUser(views.APIView):
	permission_classes = [IsAuthenticated]
	def get(self, request, format=None):

			return Response({"user":request.user.id})


class CardFileViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.FileAttachmentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)

		return CardFile.objects.filter(q).distinct()

class CardImageViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.ImageAttachmentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		return CardImage.objects.filter(q).distinct()


class CardLabelViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardLabelSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		return CardLabel.objects.filter(q).distinct()

class BoardListViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.BoardListSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(board__owner=self.request.user) | Q(board__board_memberships__user=self.request.user)
		return BoardList.objects.filter(q).distinct()

class BoardListArchivedUpdateView(UpdateAPIView):
	serializer_class = serializers.BoardListArchivedSerializer

	def get_queryset(self):
		q = Q(board__owner=self.request.user)

		return BoardList.objects.filter(q)

class BoardListOrderUpdating(views.APIView):
	permission_classes = [IsBoardOwnerOrMember]
	def patch(self, request, *args, **kwargs):
		ids = [item["id"] for item in request.data]
		q = (Q(board__owner=self.request.user) | Q(board__board_memberships__user=self.request.user)) & Q(id__in=ids)
		queryset = BoardList.objects.filter(q)

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
		q = (Q(board_list__board__owner=self.request.user) | Q(board_list__board__board_memberships__user=self.request.user)) & Q(id__in=ids)

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
	permission_classes = [WatchBoardCardPermission]

class CardWatchView(ToggleWatchMixin, views.APIView):
	serializer_class = serializers.CardWatchSerializer
	permission_classes = [WatchBoardCardPermission]


class LinkAttachmentViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.LinkAttachmentSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
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
		q = Q(board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		return Card.objects.filter(q)



class ActivitytViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.ActivitySerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):

		return Activity.objects.all()


class PublicBoardAddress(views.APIView):
	def get(self, request, *args, **kwargs):
		board_id = kwargs.get("pk")

		current_site = get_current_site(request)
		use_https = False
		board = get_object_or_404(Board, id=board_id, owner=request.user, status="public")
		protocol = "https" if use_https else "http"
		board_address = f'{protocol}//{current_site}/public/{board.short_uuid}/{board.slug}/'
		return Response({"board_address":board_address}, status=status.HTTP_200_OK)

