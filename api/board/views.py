from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
import django_filters.rest_framework
from rest_framework import viewsets, mixins, views
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, get_object_or_404, GenericAPIView, CreateAPIView, DestroyAPIView
from board.models import (
	Board, Card, CheckList, 
	ChecklistItem, Comment, 
	CardFile, CardImage, 
	CardLabel, BoardList, 
	CardMembership,BoardMembership,
	BoardWatch, LinkAttachment,
	Activity
	)
from django.contrib.sites.models import Site
from django.urls import reverse
from account.models import Notification
from board.tasks import send_email_task
from . import serializers
from .pagination import CustomCursorPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import (
	IsBoardOwner, 
	IsBoardOwnerOrMember, 
	CardMembershipPermission, 
	BoardMembershipPermission, 
	WatchBoardCardPermission,
	BoardMemberCanCreateCardRelated,
	CardRelatedObjOwnerCanEdit

	)

def get_current_site_address(request):
	current_site = get_current_site(request)
	site_name = current_site.name
	domain = current_site.domain
	protocol = "https" if request.is_secure() else "http"
	site_address = f"{protocol}://{current_site}"
	return site_name, site_address

def send_instant_notification(request, instance):
	field = instance.action_type
	
	notifications = Notification.objects.filter(email_frequency="instantly",**{field:True})
	
	site_name, site_address = get_current_site_address(request)
	activity_link = reverse("board:board_detail", kwargs={"pk":instance.board.pk})
	board_link = f"{site_address}/{activity_link}"


	for notification in notifications:
		kwargs = {
		"board":instance.board.name,
		"board_link":board_link,
		"recipient_id":notification.user.id,
		"recipient":notification.user.username,
		"recipient_email":notification.user.email,
		"activity_id":instance.id,
		"actor_user":instance.user.username,
		"site_name":site_name,
		"site_address":site_address,
		"activity_text":instance.text,
		"activity_action_type":instance.action_type
		}
		send_email_task.delay(**kwargs)


class ActivityLog:
	@staticmethod
	def log(request, user, board,board_list, card, action_type, text):
		activity = Activity.objects.create(
			user=user,
			board=board, 
			board_list=board_list, 
			card=card, 
			action_type=action_type, 
			text=text
			)

		send_instant_notification(request, activity)



UserModel = get_user_model()

class BoardViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.BoardSerializer
	permission_classes = [IsBoardOwner]

	def get_queryset(self):

		return Board.objects.filter(owner=self.request.user)
	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "create_board"
		text = f"{instance.name} created"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance, 
			board_list=None, 
			card=None, 
			action_type=action_type, 
			text=text)

	def perform_update(self, serializer):
		board = self.get_object()
		old_name = board.name
		old_status = board.status
		old_closed = board.closed
		old_background_color = board.background_color
		old_background_image = board.background_image
		
		instance = serializer.save()
		text = None
		action_type = None
		actions = []
		if old_name != instance.name:
			action_type = "edit_board_title"
			text = f"The name of the board was changed from {old_name} to {instance.name} "
			actions.append((action_type, text))

		if old_status != instance.status:
			action_type = "edit_board_status"
			text = f"The visibility of the board was changed from {old_status} to {instance.status} "
			actions.append((action_type, text))

		if old_closed != instance.closed:
			action_type = "close_board"
			text = f"The '{instance.name} board closed"
			actions.append((action_type, text))

		if (old_background_color != instance.background_color) | (old_background_image != instance.background_image):
			action_type = "edit_background"
			text = f"The '{instance.name}' board background changed"
			actions.append((action_type, text))

		for action in actions:
			ActivityLog.log(
				request=self.request,
				user=self.request.user,
				board=instance, 
				board_list=None, 
				card=None, 
				action_type=action[0], 
				text=action[1])	


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
	permission_classes = [IsAuthenticated]
	def get_queryset(self):
		q = (Q(board_memberships__user=self.request.user) | Q(owner=self.request.user)) & Q(closed=False)

		return Board.objects.filter(q).distinct()



class CardViewSet(viewsets.ModelViewSet):
	serializer_class = serializers.CardNestedSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):
		card__board_list__board__board_memberships__user=self.request.user
		q = Q(board_list__board__owner=self.request.user) | Q(board_list__board__board_memberships__user=self.request.user)

		return Card.objects.filter(q).distinct()

	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "create_card"
		text = f"The '{instance.name}' card in the {instance.board_list.name} list was created"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.board_list.board, 
			board_list=instance.board_list, 
			card=instance, 
			action_type=action_type, 
			text=text)

	def perform_update(self, serializer):
		card = self.get_object()
		old_name = card.name
		old_description = card.description
		old_start_date = card.start_date
		old_due_date = card.due_date
		old_completed = card.completed
		old_cover_image = card.cover_image
		old_cover_image_fk = card.cover_image_fk
		old_cover_color = card.cover_color
		old_board_list = card.board_list






		
		instance = serializer.save()
		text = None
		action_type = None
		actions = []
		if old_name != instance.name:
			action_type = "edit_card_title"
			text = f"The name of the card was was changed from {old_name} to {instance.name} "
			actions.append((action_type, text))

		if old_description != instance.description:
			action_type = "edit_card_description"
			text = f"The description of {instance.name} card was changed"
			actions.append((action_type, text))


		if old_start_date != instance.start_date:
			action_type = "edit_start_date"
			text = f"The Start Date of {instance.name} card was changed"
			actions.append((action_type, text))

		if old_due_date != instance.due_date:
			action_type = "edit_due_date"
			text = f"The Due Date of {instance.name} card was changed"
			actions.append((action_type, text))

		if old_completed != instance.completed:
			action_type = "edit_card_completed"
			text = f"The completeness of the '{instance.name}' card is changed to '{instance.completed}'"
			actions.append((action_type, text))

		if (instance.cover_image==None) and (instance.cover_image_fk==None) and (instance.cover_color==""):
			action_type = "remove_card_cover"
			text = f"Cover was removed from '{instance.name}' card"
			actions.append((action_type, text))	
		elif (old_cover_image != instance.cover_image) or (old_cover_image_fk != instance.cover_image_fk) or (old_cover_color != instance.cover_color):
			action_type = "set_card_cover"
			text = f"Cover was set to '{instance.name}' card"
			actions.append((action_type, text))	

		if old_board_list != instance.board_list:
			action_type = "move_card"
			text = f"'{instance.name}' card moved from '{old_board_list.name}' list to '{instance.board_list.name}' list"
			actions.append((action_type, text))

		for action in actions:
			ActivityLog.log(
				request=self.request,
				user=self.request.user,
				board=instance.board_list.board, 
				board_list=instance.board_list, 
				card=instance, 
				action_type=action[0], 
				text=action[1])	


class CardArchivedUpdateView(UpdateAPIView):
	serializer_class = serializers.CardArchivedSerializer

	def get_queryset(self):

		q = Q(board_list__board__owner=self.request.user)

		return Card.objects.filter(q).distinct()

	def perform_update(self, serializer):
		card = self.get_object()
		old_archived = card.archived


		instance = serializer.save()
		
		text = None
		action_type = None
		actions = []

		if (old_archived != instance.archived) and  (instance.archived == True):
			action_type = "archive_card"
			text = f"The '{instance.name}' card was archived"
			actions.append((action_type, text))	
		if (old_archived != instance.archived) and  (instance.archived == False):
			action_type = "unarchive_card"
			text = f"The '{instance.name}' card was unarchived"
			actions.append((action_type, text))	
		for action in actions:
			ActivityLog.log(
				request=self.request,
				user=self.request.user,
				board=instance.board_list.board, 
				board_list=instance.board_list, 
				card=instance, 
				action_type=action[0], 
				text=action[1])	
class ChecklistViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CheckListSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):
		
		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		
		return CheckList.objects.filter(q).distinct()

	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_checklist"
		text = f"'{instance.name}' checklist added"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text)

	def perform_update(self, serializer):
		checklist = self.get_object()
		old_name = checklist.name

		
		instance = serializer.save()
		text = None
		action_type = None
		actions = []
		if old_name != instance.name:
			action_type = "edit_checklist_name"
			text = f"The name of the checklist was changed from '{old_name}' to '{instance.name}' "
			actions.append((action_type, text))

		for action in actions:
			ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action[0], 
			text=action[1])

	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_checklist"
		text = f"The '{instance.name}' checklist in '{instance.card.name}' card was removed"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text
		)

class ChecklistItemViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CheckListItemSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(checklist__card__board_list__board__owner=self.request.user) | Q(checklist__card__board_list__board__board_memberships__user=self.request.user)
		
		return ChecklistItem.objects.filter(q).distinct()

	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_checklist_item"
		text = f"'{instance.name}' item added to '{instance.checklist.name}' in '{instance.checklist.card.name}' card"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.checklist.card.board_list.board, 
			board_list=instance.checklist.card.board_list, 
			card=instance.checklist.card, 
			action_type=action_type, 
			text=text)

	def perform_update(self, serializer):
		checklist_item = self.get_object()
		old_name = checklist_item.name
		old_is_completed = checklist_item.is_completed

		
		instance = serializer.save()
		text = None
		action_type = None
		actions = []
		if old_name != instance.name:
			action_type = "edit_checklist_item_name"
			text = f"The name of the item was changed from '{old_name}' to '{instance.name}' "
			actions.append((action_type, text))

		if old_is_completed != instance.is_completed:
			action_type = "edit_checklist_item_completed"
			text = f"The completeness of '{instance.name}' item in '{instance.checklist.name}' checklist changed to '{instance.is_completed}' "
			actions.append((action_type, text))

		for action in actions:
			ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.checklist.card.board_list.board, 
			board_list=instance.checklist.card.board_list, 
			card=instance.checklist.card, 
			action_type=action[0], 
			text=action[1])

	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_checklist_item"
		text = f"The '{instance.name}' item in '{instance.checklist.name}' checklist was removed"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.checklist.card.board_list.board, 
			board_list=instance.checklist.card.board_list, 
			card=instance.checklist.card, 
			action_type=action_type, 
			text=text
		)
class CommentViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardCommentSerializer
	permission_classes = [BoardMemberCanCreateCardRelated, CardRelatedObjOwnerCanEdit]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		
		return Comment.objects.filter(q).distinct()

	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_comment"
		text = f"'{instance.user.username}' adds Comment to the '{instance.card.name}' card"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text)


	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_comment"
		text = f"'{instance.user.username}' remove his comment"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text
		)



class CurrentUser(views.APIView):
	permission_classes = [IsAuthenticated]
	def get(self, request, format=None):

			return Response({"user":request.user.id})


class CardFileViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.FileAttachmentSerializer
	permission_classes = [BoardMemberCanCreateCardRelated, CardRelatedObjOwnerCanEdit]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)

		return CardFile.objects.filter(q).distinct()
	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_attachment"
		text = f"'{instance.get_name()}' attachment added to '{instance.card.name}'"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text)


	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_attachment"
		text = f"The '{instance.get_name()}' attachment in '{instance.card.name}' card was removed"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text
		)

class CardImageViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.ImageAttachmentSerializer
	permission_classes = [BoardMemberCanCreateCardRelated, CardRelatedObjOwnerCanEdit]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		return CardImage.objects.filter(q).distinct()

	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_attachment"
		text = f"'{instance.get_name()}' attachment added to '{instance.card.name}'"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text)


	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_attachment"
		text = f"The '{instance.get_name()}' attachment in '{instance.card.name}' card was removed"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text
		)
class CardLabelViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardLabelSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		return CardLabel.objects.filter(q).distinct()
	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_card_label"
		text = f"'{instance.name}' label added to'{instance.card.name}' card"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text)

	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_card_label"
		text = f"The '{instance.name}' label in '{instance.card.name}' card was removed"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text
		)
class BoardListViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.BoardListSerializer
	permission_classes = [IsBoardOwnerOrMember]

	def get_queryset(self):

		q = Q(board__owner=self.request.user) | Q(board__board_memberships__user=self.request.user)
		return BoardList.objects.filter(q).distinct()

	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "create_list"
		text = f"'{instance.name}' list added to board"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.board, 
			board_list=instance, 
			card=None, 
			action_type=action_type, 
			text=text)

	def perform_update(self, serializer):
		board_list = self.get_object()
		old_name = board_list.name

		
		instance = serializer.save()
		text = None
		action_type = None
		actions = []
		if old_name != instance.name:
			action_type = "edit_list_title"
			text = f"The name of the list was changed from '{old_name}' to '{instance.name}' "
			actions.append((action_type, text))

		for action in actions:
			ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.board, 
			board_list=instance, 
			card=None, 
			action_type=action[0], 
			text=action[1])

	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_list"
		text = f"The '{instance.name}' list was removed"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.board, 
			board_list=instance, 
			card=None, 
			action_type=action_type, 
			text=text
		)

class BoardListArchivedUpdateView(UpdateAPIView):
	serializer_class = serializers.BoardListArchivedSerializer

	def get_queryset(self):
		q = Q(board__owner=self.request.user)

		return BoardList.objects.filter(q).distinct()

	def perform_update(self, serializer):
		board_list = self.get_object()
		old_archived = board_list.archived

		
		instance = serializer.save()
		text = None
		action_type = None
		actions = []
		if (old_archived != instance.archived) and (instance.archived == True):
			action_type = "archive_list"
			text = f"The '{instance.name}' list was archived"
			actions.append((action_type, text))
		elif (old_archived != instance.archived) and (instance.archived == False):
			action_type = "unarchive_list"
			text = f"The '{instance.name}' list was unarchived"
			actions.append((action_type, text))
		for action in actions:
			ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.board, 
			board_list=instance, 
			card=None, 
			action_type=action[0], 
			text=action[1])
class BoardListOrderUpdating(views.APIView):

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
			instances = serializer.save()

			action_type = "change_lists_order"
			text = f"Lists order changed"
			ActivityLog.log(
				request=self.request,
				user=self.request.user,
				board=instances[0].board, 
				board_list=None, 
				card=None, 
				action_type=action_type, 
				text=text)
			return Response(serializer.data, status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardOrderUpdating(views.APIView):

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
			instances = serializer.save()

			action_type = "change_cards_order"
			text = f"Cards of '{instances[0].board_list.name}' list, order changed"
			ActivityLog.log(
				request=self.request,
				user=self.request.user,
				board=instances[0].board_list.board, 
				board_list=instances[0].board_list, 
				card=None, 
				action_type=action_type, 
				text=text)
			return Response(serializer.data, status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardMemberViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.CardMembershipSerializer
	permission_classes = [CardMembershipPermission]
	http_method_names = ['delete', 'post']
	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user)
		return CardMembership.objects.filter(q).distinct()

	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_card_member"
		text = f"'{instance.user.username}' added to '{instance.card.name}'"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text)


	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_card_member"
		text = f"The '{instance.user.username}' removed from '{instance.card.name}' card"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text
		)
class BoardMemberViewSet(viewsets.ModelViewSet):

	serializer_class = serializers.BoardMembershipSerializer
	permission_classes = [BoardMembershipPermission]
	def get_queryset(self):

		q = Q(board__owner=self.request.user)
		return BoardMembership.objects.filter(q).distinct()

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
	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_board_member"
		text = f"'{instance.user.username}' added to '{instance.board.name}'"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.board, 
			board_list=None, 
			card=None, 
			action_type=action_type, 
			text=text)


	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_board_member"
		text = f"The '{instance.user.username}' removed from board"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.board, 
			board_list=None, 
			card=None, 
			action_type=action_type, 
			text=text
		)

class ToggleWatchMixin:
	def post(self, request, *args, **kwargs):
		
		serializer = self.serializer_class(
			data=request.data,
			context={"request":request}
			)
		if serializer.is_valid():
			instance = serializer.save()
			if isinstance(serializer, serializers.CardWatchSerializer):
				
				if request.data.get("watch")==True:
					action_type = "watch_card"
					text = f"{instance.card.name} Card started being watched"
				else:
					action_type = "unwatch_card"
					text = f"{instance.card.name} Card stopped being watched"



				ActivityLog.log(
					request=self.request,
					user=self.request.user,
					board=instance.card.board_list.board, 
					board_list=instance.card.board_list, 
					card=instance.card, 
					action_type=action_type, 
					text=text
				)
			elif isinstance(serializer, serializers.BoardWatchSerializer):
				
				if request.data.get("watch")==True:
					action_type = "watch_board"
					text = f"{instance.board.name} Board started being watched"
				else:
					action_type = "unwatch_board"
					text = f"{instance.board.name} Board stopped being watched"



				ActivityLog.log(
					request=self.request,
					user=self.request.user,
					board=instance.board, 
					board_list=None, 
					card=None, 
					action_type=action_type, 
					text=text
				)	

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
	permission_classes = [BoardMemberCanCreateCardRelated, CardRelatedObjOwnerCanEdit]

	def get_queryset(self):

		q = Q(card__board_list__board__owner=self.request.user) | Q(card__board_list__board__board_memberships__user=self.request.user)
		return LinkAttachment.objects.filter(q).distinct()
	def perform_create(self, serializer):
		instance = serializer.save()
		action_type = "add_attachment"
		text = f"'{instance.file}' link added to '{instance.card.name}'"
		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text)


	def perform_destroy(self, instance):
		instance.delete()

		action_type = "remove_attachment"
		text = f"The '{instance.file}' link in '{instance.card.name}' card was removed"

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.card.board_list.board, 
			board_list=instance.card.board_list, 
			card=instance.card, 
			action_type=action_type, 
			text=text
		)

class CopyCardView(GenericAPIView):
	serializer_class = serializers.CardNestedSerializer



	def post(self, request, *args, **kwargs):
		instance = self.get_object()
		instance.pk = None
		instance.order = None
		instance._state.adding = True
		instance.save()

		action_type = "copy_card"
		text = f"The '{instance.name}' card copied "

		ActivityLog.log(
			request=self.request,
			user=self.request.user,
			board=instance.board_list.board, 
			board_list=instance.board_list, 
			card=instance, 
			action_type=action_type, 
			text=text
		)
		serializer = self.get_serializer(instance)
		return Response(serializer.data)

	def get_queryset(self):
		q = Q(board_list__board__owner=self.request.user) | Q(board_list__board__board_memberships__user=self.request.user)
		return Card.objects.filter(q).distinct()



class ActivitytView(ListAPIView):

	serializer_class = serializers.ActivitySerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		board_id = self.kwargs.get("board")
		
		return Activity.objects.filter(board=board_id)



class PublicBoardAddress(views.APIView):
	def get(self, request, *args, **kwargs):
		board_id = kwargs.get("pk")


		board = get_object_or_404(Board, id=board_id, owner=request.user, status="public")
		site_name, site_address = get_current_site_address(request)

		board_address = f'{site_address}/public/{board.short_uuid}/{board.slug}/'
		return Response({"board_address":board_address}, status=status.HTTP_200_OK)



class ProfileUpdateView(UpdateAPIView):
	serializer_class = serializers.ProfileSerializer
	def get_object(self):
		return self.request.user.profile


class UserUpdateView(UpdateAPIView):
	serializer_class = serializers.UserSerializer
	def get_object(self):
		return self.request.user



class CardListView(ListAPIView):
	serializer_class = serializers.CardNestedSerializer
	pagination_class = CustomCursorPagination
	filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
	filterset_fields = ['archived',]

	def get_queryset(self):
		return Card.objects.filter(board_list__board__owner=self.request.user)




def send_deletion_notification(request, user_data):
	username = user_data.get("username")
	user_email = user_data.get("email")
	site_name, site_address = get_current_site_address(request)

	text_content = render_to_string("board/email/delete_account.txt", {"site_name":site_name, "site_address":site_address})
	html_content = render_to_string("board/email/delete_account.html", {"site_name":site_name, "site_address":site_address})

	email = EmailMultiAlternatives(
			subject=f"Account Deleted",
			body=text_content,
			from_email=settings.DEFAULT_FROM_EMAIL,
			to=[user_email]
		)

	email.attach_alternative(html_content, "text/html")
	email.send(fail_silently=False)


class UserDestroyView(DestroyAPIView):

	def perform_destroy(self, instance):
		user_data = {
		"id":instance.id,
		"username":instance.username,
		"email":instance.email
		}
		instance.delete()
		send_deletion_notification(self.request, user_data)

	def get_object(self):
		return self.request.user


class SettingConfig(views.APIView):
	permission_classes = [IsAuthenticated]
	def get(self, request, *args, **kwargs):
		
		return Response({"host_async_ability":settings.HOST_ASYNC_ABILITY, "notification_setting":request.user.notification.id})



class NotificationSettingViewset(
							mixins.RetrieveModelMixin,   
							mixins.UpdateModelMixin,     
							viewsets.GenericViewSet):
	serializer_class = serializers.NotificationSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		return self.request.user.notification


def message_feedback(request, name, user_email, message):
	site_name, site_address = get_current_site_address(request)

	text_content = render_to_string("board/email/received_message.txt", {"site_name":site_name, "site_address":site_address, "name":name, "email":user_email, "message":message})
	html_content = render_to_string("board/email/received_message.html", {"site_name":site_name, "site_address":site_address, "name":name, "email":user_email, "message":message})

	email = EmailMultiAlternatives(
			subject=f"Your message has been received",
			body=text_content,
			from_email=settings.DEFAULT_FROM_EMAIL,
			to=[user_email]
		)

	email.attach_alternative(html_content, "text/html")
	email.send(fail_silently=False)
class ContactMessage(CreateAPIView):
	permission_classes = [AllowAny]
	serializer_class = serializers.EmailInboxSerializer

	def perform_create(self, serializer):
		instance = serializer.save()
		message_feedback(self.request, instance.name, instance.email, instance.message)