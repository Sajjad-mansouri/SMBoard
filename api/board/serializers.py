import mimetypes
from rest_framework import serializers
from django.contrib.auth import get_user_model
from board.models import Board, Card, BoardList, BoardMembership, CheckList, ChecklistItem, Comment, CardFile, CardImage

UserModel = get_user_model()



class UserSerializer(serializers.ModelSerializer):
	profile_image = serializers.SerializerMethodField()
	fullname = serializers.SerializerMethodField()

	class Meta:
		model = UserModel
		fields = ["id", "username", "email", "profile_image", "fullname"]

	def get_profile_image(self, obj):
		return obj.profile.profile_image.url if obj.profile.profile_image else ""

	def get_fullname(self, obj):
		return obj.get_full_name()

class BoardSerializer(serializers.ModelSerializer):
	# user = UserSerializer()
	cards = serializers.SerializerMethodField()
	is_owner = serializers.SerializerMethodField()

	class Meta:
		model = Board
		fields = ["id", "owner", "name", "status", "background_color", "background_image", "cards", "is_owner", "closed"]

	def get_cards(self, obj):
		return 12

	def get_is_owner(self, obj):
		request = self.context["request"]
		return obj.owner_id == request.user.id 

	def to_internal_value(self, data):
		request = self.context["request"]
		data["owner"] = request.user.id
		return super().to_internal_value(data)



class CardSerializer(serializers.ModelSerializer):
	board_list = serializers.SerializerMethodField()
	board = serializers.SerializerMethodField()
	labels = serializers.SerializerMethodField()


	class Meta:
		model = Card
		fields = ["id", "board_list", "name", "due_date", "board", "labels", "completed"]

	def get_board_list(self, obj):
		return obj.board_list.name

	def get_board(self, obj):
		return obj.board_list.board.name

	def get_labels(self, obj):
		return obj.card_labels.values_list("name", flat=True)

class CheckListItems(serializers.ModelSerializer):
	class Meta:
		model = ChecklistItem
		fields = ["id", "name", "is_completed"]

class CheckListSerializer(serializers.ModelSerializer):
	checklist_items = CheckListItems(many=True)
	class Meta:
		model = CheckList
		fields = ["id", "name", "checklist_items"]

class CardCommentSerializer(serializers.ModelSerializer):
	created_timestamp = serializers.SerializerMethodField()
	updated_timestamp = serializers.SerializerMethodField()

	class Meta:
		model = Comment
		fields = ["id", "user", "content", "created_timestamp", "updated_timestamp", "edited"]	

	def get_created_timestamp(self, obj):
		return obj.created.timestamp()

	def get_updated_timestamp(self, obj):
		return obj.updated.timestamp()

class FileAttachments(serializers.ModelSerializer):
	file_type = serializers.SerializerMethodField()
	name = serializers.SerializerMethodField()
	upload_at = serializers.SerializerMethodField()


	class Meta:
		model = CardFile
		fields = ["id", "name", "description", "file", "file_type", "upload_at", "user"]

	def get_file_type(self, obj):
		mime_type, encoding = mimetypes.guess_type(obj.file.name)
		return mime_type	

	def get_name(self, obj):
		name_loc = obj.file.name
		name = name_loc.rsplit("/",1)[1]
		return name

	def get_upload_at(self, obj):
		return obj.created.timestamp()

class ImageAttachments(FileAttachments):
	class Meta(FileAttachments.Meta):
		pass

class CardNestedSerializer(CardSerializer):
	members = serializers.SerializerMethodField()
	card_checklists = CheckListSerializer(many=True)
	card_comments = CardCommentSerializer(many=True)
	start_date = serializers.DateField(
		format="%Y-%m-%d", 
		input_formats=['%Y-%m-%d']
	)
	
	# For "2026-05-28T12:12"
	due_date = serializers.DateTimeField(
		format="%Y-%m-%dT%H:%M", 
		input_formats=['%Y-%m-%dT%H:%M', 'iso-8601']
	)
	watched = serializers.SerializerMethodField()
	cardfile_set = FileAttachments(many=True)
	cardimage_set = ImageAttachments(many=True)

	class Meta(CardSerializer.Meta):
		extra_fields = [
		"description", "start_date", 
		"archived", "cover_image", 
		"cover_color", "members", "card_checklists",
		"card_comments", "watched", "cardfile_set",
		"cardimage_set"

		]
		fields = CardSerializer.Meta.fields +  extra_fields

	def get_members(self, obj):
		return obj.card_memberships.values_list("user_id", flat=True)

	def get_watched(self, obj):
		request = self.context["request"]
		return obj.card_cardwatchs.filter(user=request.user, watch=True).exists()

class BoardMembership(serializers.ModelSerializer):
	user = UserSerializer()

	class Meta:
		model = BoardMembership
		fields = ["id", "user", "member_type", "accepted"]


class BoardListSerializer(serializers.ModelSerializer):
	list_cards = CardNestedSerializer(many=True)
	class Meta:
		model = BoardList
		fields = ["id", "order", "name", "cover_image", "cover_color", "list_cards", "archived"]

class BoardNestedSerializer(BoardSerializer):
	board_lists = BoardListSerializer(many=True)
	board_watched = serializers.SerializerMethodField()
	board_memberships = BoardMembership(many=True)
	class Meta(BoardSerializer.Meta):
		fields = BoardSerializer.Meta.fields + ["board_lists", "board_watched", "board_memberships"]

	def get_board_watched(self, obj):
		request = self.context["request"]
		return obj.board_boardwatchs.filter(user=request.user, watch=True).exists()