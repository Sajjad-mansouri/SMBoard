from rest_framework import serializers
from board.models import Board

class BoardSerializer(serializers.ModelSerializer):
	cards = serializers.SerializerMethodField()
	class Meta:
		model = Board
		fields = ["id", "user", "name", "status", "background_color", "background_image", "cards"]

	def get_cards(self, obj):
		return 12