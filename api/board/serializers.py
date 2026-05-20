from rest_framework import serializers
from django.contrib.auth import get_user_model
from board.models import Board

UserModel = get_user_model()

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserModel
		fields = ["id", "username", "email"]

class BoardSerializer(serializers.ModelSerializer):
	# user = UserSerializer()
	cards = serializers.SerializerMethodField()
	class Meta:
		model = Board
		fields = ["id", "user", "name", "status", "background_color", "background_image", "cards"]

	def get_cards(self, obj):
		return 12

	def to_internal_value(self, data):
		request = self.context["request"]
		data["user"] = request.user.id
		return super().to_internal_value(data)