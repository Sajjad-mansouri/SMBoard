import mimetypes
from rest_framework import serializers
from django.contrib.auth import get_user_model
from board.models import Board, Card, BoardList, BoardMembership, CheckList, ChecklistItem, Comment, CardFile, CardImage, CardLabel
from rest_framework.generics import get_object_or_404

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

class CardLabelSerializer(serializers.ModelSerializer):
	class Meta:
		model = CardLabel
		fields = ["id", "name", "color", "card"]

class CardSerializer(serializers.ModelSerializer):
	board_list = serializers.SerializerMethodField()
	board = serializers.SerializerMethodField()
	card_labels = CardLabelSerializer(many=True)
	labels = serializers.SerializerMethodField()


	class Meta:
		model = Card
		fields = ["id", "board_list", "name", "due_date", "board", "labels", "card_labels", "completed"]

	def get_board_list(self, obj):
		return obj.board_list.name

	def get_board(self, obj):
		return obj.board_list.board.name

	def get_labels(self, obj):
		return obj.card_labels.values_list("id", flat=True)

class CheckListItemSerializer(serializers.ModelSerializer):
	class Meta:
		model = ChecklistItem
		fields = ["id", "name", "is_completed", "checklist"]

class CheckListSerializer(serializers.ModelSerializer):
	checklist_items = CheckListItemSerializer(many=True, read_only=True)
	class Meta:
		model = CheckList
		fields = ["id", "name", "checklist_items", "card"]


class CardCommentSerializer(serializers.ModelSerializer):
	timestamp = serializers.SerializerMethodField()
	reply = serializers.SerializerMethodField()



	class Meta:
		model = Comment
		fields = ["id", "user", "content", "timestamp", "edited", "card", "reply"]	

	def to_internal_value(self, data):
		request = self.context["request"]
		data["user"] = request.user.id
		return super().to_internal_value(data)
	def create(self, validated_data):
		reply_type = self.initial_data.get("reply_type")
		reply_id = self.initial_data.get("reply_id")
		image_types = ["image", "png", "jpeg"]
		file_types = ["text", "plain", "csv","zip", "rar","file"]

		reply_img_attachment = False
		reply_file_attachment = False
		reply_content_object = None
		if reply_type:
			types = reply_type.split("/")
			reply_img_attachment = any(item in image_types for item in types)
			reply_file_attachment = any(item in file_types for item in types)

		if reply_img_attachment:
			reply_content_object = get_object_or_404(CardImage, id=int(reply_id))
		elif reply_file_attachment:
			reply_content_object = get_object_or_404(CardFile, id=int(reply_id))

		obj = Comment.objects.create(reply_content_object=reply_content_object, **validated_data)


		return obj

	def get_timestamp(self, obj):

		if obj.updated:
			return obj.updated.timestamp()
		else:
			obj.created.timestamp()

	def get_reply(self, obj):

		if obj.reply_content_object:
			mime_type, encoding = mimetypes.guess_type(obj.reply_content_object.file.name)
			return {"name":obj.reply_content_object.get_name(), "id":obj.reply_content_object.id, "type":mime_type}
		else:
			return None



class FileAttachmentSerializer(serializers.ModelSerializer):
	file_type = serializers.SerializerMethodField()
	display_name = serializers.SerializerMethodField()
	upload_at = serializers.SerializerMethodField()


	class Meta:
		model = CardFile
		fields = ["id", "name", "display_name","description", "file", "file_type", "upload_at", "user", "card"]

	def to_internal_value(self, data):
		request = self.context["request"]
		data["user"] = request.user.id
		return super().to_internal_value(data)

	def get_file_type(self, obj):
		mime_type, encoding = mimetypes.guess_type(obj.file.name)
		return mime_type	

	def get_display_name(self, obj):
		name_loc = obj.file.name
		name = name_loc.rsplit("/",1)[1]
		extension = name.split(".")[1]
		if obj.name:
			return ".".join([obj.name, extension])
		return name

	def get_upload_at(self, obj):
		return obj.created.timestamp()

class ImageAttachmentSerializer(FileAttachmentSerializer):
	class Meta(FileAttachmentSerializer.Meta):
		model = CardImage

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
	cover_img = serializers.SerializerMethodField()
	watched = serializers.SerializerMethodField()

	cardfile_set = FileAttachmentSerializer(many=True)
	cardimage_set = ImageAttachmentSerializer(many=True)

	class Meta(CardSerializer.Meta):
		extra_fields = [
		"description", "start_date", 
		"archived", "cover_image","cover_image_fk","cover_img",
		"cover_color", "members", "card_checklists",
		"card_comments", "watched", "cardfile_set",
		"cardimage_set"

		]
		fields = CardSerializer.Meta.fields +  extra_fields

	def get_cover_img(self, obj):
		if obj.cover_image:
			return obj.cover_image.url
		elif obj.cover_image_fk:

			return obj.cover_image_fk.file.url
		else:
			return ""
	def get_members(self, obj):
		return obj.card_memberships.values_list("user_id", flat=True)

	def get_watched(self, obj):
		request = self.context["request"]
		return obj.card_cardwatchs.filter(user=request.user, watch=True).exists()
	def is_valid(self, *, raise_exception=False):
		err = super().is_valid(raise_exception=False)
		print("error",err, self._errors)
		return err
class BoardMembership(serializers.ModelSerializer):
	user = UserSerializer()

	class Meta:
		model = BoardMembership
		fields = ["id", "user", "member_type", "accepted"]


class BoardListSerializer(serializers.ModelSerializer):
	list_cards = CardNestedSerializer(many=True, read_only=True)
	class Meta:
		model = BoardList
		fields = ["id", "order", "name", "cover_image", "cover_color", "list_cards", "archived","board"]


class BoardNestedSerializer(BoardSerializer):
	board_lists = BoardListSerializer(many=True)
	board_watched = serializers.SerializerMethodField()
	board_memberships = BoardMembership(many=True)
	class Meta(BoardSerializer.Meta):
		fields = BoardSerializer.Meta.fields + ["board_lists", "board_watched", "board_memberships"]

	def get_board_watched(self, obj):
		request = self.context["request"]
		return obj.board_boardwatchs.filter(user=request.user, watch=True).exists()

