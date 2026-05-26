from rest_framework import serializers
from django.contrib.auth import get_user_model
from board.models import Board, Card, BoardList, BoardMembership

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
		fields = ["id", "board_list", "name", "due_date", "board", "labels"]

	def get_board_list(self, obj):
		return obj.board_list.name

	def get_board(self, obj):
		return obj.board_list.board.name

	def get_labels(self, obj):
		return obj.card_labels.values_list("name", flat=True)


class CardNestedSerializer(CardSerializer):
	class Meta(CardSerializer.Meta):

		fields = CardSerializer.Meta.fields 

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