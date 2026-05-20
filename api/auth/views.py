from django.contrib.auth import authenticate, login
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
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