from rest_framework import serializers
from django.contrib.auth import get_user_model
from board.models import Board, Card

UserModel = get_user_model()



class UserSerializer(serializers.ModelSerializer):
	profile_image = serializers.SerializerMethodField()
	class Meta:
		model = UserModel
		fields = ["id", "username", "email", "profile_image"]

	def get_profile_image(self, obj):
		return obj.profile.profile_image.url if obj.profile.profile_image else ""

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