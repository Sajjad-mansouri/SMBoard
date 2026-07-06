from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
import time
class LoginApiView(APIView):
	permission_classes = []
	def post(self, request, *args, **kwargs):

		username = request.data.get("username")
		password = request.data.get("password")

		user = authenticate(username=username, password=password)

		if not user:
			return Response({"error":"Invalid Credentials"}, status=401)

		login(request, user)
		refresh = RefreshToken.for_user(user)
		return Response({
			"access": str(refresh.access_token),
			"refresh": str(refresh)
			})

class LogoutApiView(APIView):
	def post(self, request, *args, **kwargs):
		"""Logout may be done via POST."""

		refresh_token = request.data.get("refresh")
		if not refresh_token:
			return Response({"error":"Logout failed"}, status=status.HTTP_400_BAD_REQUEST)

		try:
			token = RefreshToken(refresh_token)
			token.blacklist()
		except Exception as e:
			return Response({"error":"Logout failed"}, status=status.HTTP_400_BAD_REQUEST)
		auth_logout(request)
		return Response({"message":"Successfuly logged out"},status=status.HTTP_200_OK)