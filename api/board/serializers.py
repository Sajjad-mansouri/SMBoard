import mimetypes
from rest_framework import serializers
from django.contrib.auth import get_user_model
from board.models import (
	Board, Card, BoardList, 
	BoardMembership, CheckList, 
	ChecklistItem, Comment, CardFile, 
	CardImage, CardLabel,CardMembership,
	BoardWatch, CardWatch, LinkAttachment
	)
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

	board = serializers.SerializerMethodField()
	card_labels = CardLabelSerializer(many=True,read_only=True)
	labels = serializers.SerializerMethodField()


	class Meta:
		model = Card
		fields = ["id", "board_list", "name", "due_date", "board", "labels", "card_labels", "completed", "order"]



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
		reply_link_attachment = False
		reply_content_object = None
		if reply_type:
			types = reply_type.split("/")
			reply_img_attachment = any(item in image_types for item in types)
			reply_file_attachment = any(item in file_types for item in types)
			reply_link_attachment = reply_type == "link"

		if reply_img_attachment:
			reply_content_object = get_object_or_404(CardImage, id=int(reply_id))
		elif reply_file_attachment:
			reply_content_object = get_object_or_404(CardFile, id=int(reply_id))
		elif reply_link_attachment:
			reply_content_object = get_object_or_404(LinkAttachment, id=int(reply_id))



		obj = Comment.objects.create(reply_content_object=reply_content_object, **validated_data)


		return obj

	def get_timestamp(self, obj):

		if obj.updated:
			return obj.updated.timestamp()
		else:
			obj.created.timestamp()

	def get_reply(self, obj):

		if obj.reply_content_object:
			if isinstance(obj.reply_content_object, LinkAttachment):
				return {"name":obj.reply_content_object.file, "id":obj.reply_content_object.id, "type":"link"}
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
		if isinstance(obj, LinkAttachment):
			return "link"
		mime_type, encoding = mimetypes.guess_type(obj.file.name)
		return mime_type	

	def get_display_name(self, obj):
		if isinstance(obj, LinkAttachment):
			return obj.file 
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

class LinkAttachmentSerializer(FileAttachmentSerializer):
	class Meta(FileAttachmentSerializer.Meta):
		model = LinkAttachment

class CardMembershipSerializer(serializers.ModelSerializer):
	class Meta:
		model = CardMembership
		fields = ["id", "user", "card"]


class CardNestedSerializer(CardSerializer):
	card_memberships = CardMembershipSerializer(many=True, read_only=True)
	card_checklists = CheckListSerializer(many=True, read_only=True)
	card_comments = CardCommentSerializer(many=True,read_only=True)
	start_date = serializers.DateField(
		format="%Y-%m-%d", 
		input_formats=['%Y-%m-%d'],
		required=False,
		allow_null=True
	)
	
	# For "2026-05-28T12:12"
	due_date = serializers.DateTimeField(
		format="%Y-%m-%dT%H:%M", 
		input_formats=['%Y-%m-%dT%H:%M', 'iso-8601'],
		required=False,
		allow_null=True
	)
	cover_img = serializers.SerializerMethodField()
	watched = serializers.SerializerMethodField()

	cardfile_set = FileAttachmentSerializer(many=True, read_only=True)
	cardimage_set = ImageAttachmentSerializer(many=True, read_only=True)
	linkattachment_set= LinkAttachmentSerializer(many=True, read_only=True)

	class Meta(CardSerializer.Meta):
		extra_fields = [
		"description", "start_date", 
		"archived", "cover_image","cover_image_fk","cover_img",
		"cover_color", "card_memberships", "card_checklists",
		"card_comments", "watched", "cardfile_set",
		"cardimage_set","linkattachment_set"

		]
		fields = CardSerializer.Meta.fields +  extra_fields


	def get_cover_img(self, obj):
		if obj.cover_image:
			return obj.cover_image.url
		elif obj.cover_image_fk:

			return obj.cover_image_fk.file.url
		else:
			return ""


	def get_watched(self, obj):
		request = self.context["request"]
		return obj.card_cardwatchs.filter(user=request.user, watch=True).exists()

	def to_internal_value(self, data):
		print(data)
		return super().to_internal_value(data)
	def is_valid(self, *, raise_exception=False):
		err = super().is_valid(raise_exception=False)
		print(self._errors)
		return err
class BoardMembershipSerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only=True)
	user_id = serializers.PrimaryKeyRelatedField(queryset=UserModel.objects.all(), source="user",write_only=True)
	class Meta:
		model = BoardMembership
		fields = ["id", "user", "member_type", "accepted", "board", "user_id"]

	def to_internal_value(self, data):
		print("data", data)
		return super().to_internal_value(data)
	def is_valid(self, *, raise_exception=False):
		err = super().is_valid(raise_exception=False)
		print(self._errors)
		return err
class CustomListSerializer(serializers.ListSerializer):
	def update(self, instance, validated_data):

		list_mapping = {board_list.id: board_list for board_list in instance}
		data_mapping = {item['id']: item for item in validated_data}
		# Perform creations and updates.
		ret = []
		for list_id, data in data_mapping.items():
			board_list = list_mapping.get(list_id, None)
			if board_list :
				ret.append(self.child.update(board_list, data))
		return ret
class BoardListSerializer(serializers.ModelSerializer):
	list_cards = CardNestedSerializer(many=True, read_only=True)
	class Meta:
		model = BoardList
		fields = ["id", "order", "name", "cover_image", "cover_color", "list_cards", "archived","board"]


class BoardListOrderSerializer(BoardListSerializer):
	id = serializers.IntegerField()
	class Meta(BoardListSerializer.Meta):
		list_serializer_class = CustomListSerializer

class BoardNestedSerializer(BoardSerializer):
	board_lists = BoardListSerializer(many=True)
	board_watched = serializers.SerializerMethodField()
	board_memberships = BoardMembershipSerializer(many=True)
	class Meta(BoardSerializer.Meta):
		fields = BoardSerializer.Meta.fields + ["board_lists", "board_watched", "board_memberships"]

	def get_board_watched(self, obj):
		request = self.context["request"]
		print("watched",obj.board_boardwatchs.filter(user=request.user, watch=True).exists())
		return obj.board_boardwatchs.filter(user=request.user, watch=True).exists()





class CardOrderSerializer(CardSerializer):
	id = serializers.IntegerField()
	class Meta(CardSerializer.Meta):
		list_serializer_class = CustomListSerializer

class BoardWatchSerializer(serializers.ModelSerializer):
	class Meta:
		model = BoardWatch
		fields = ["user", "board", "watch", "id"]

	def to_internal_value(self, data):
		request = self.context["request"]
		data["user"] = request.user.id
		print(data)
		return super().to_internal_value(data)

	def create(self, validated_data):
		board = validated_data.get("board")
		user = validated_data.get("user")
		watch = validated_data.get("watch")

		obj, created = BoardWatch.objects.get_or_create(board=board, user=user)
		obj.watch = watch
		obj.save()
		return obj


class CardWatchSerializer(serializers.ModelSerializer):
	class Meta:
		model = CardWatch
		fields = ["user", "card", "watch", "id"]

	def to_internal_value(self, data):
		request = self.context["request"]
		data["user"] = request.user.id
		print(data)
		return super().to_internal_value(data)

	def create(self, validated_data):
		board = validated_data.get("card")
		user = validated_data.get("user")
		watch = validated_data.get("watch")

		obj, created = CardWatch.objects.get_or_create(card=board, user=user)
		obj.watch = watch
		obj.save()
		return obj