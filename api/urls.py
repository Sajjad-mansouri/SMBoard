from django.urls import path
from rest_framework_simplejwt.views import (
		TokenObtainPairView,
		TokenRefreshView,
		TokenVerifyView
	)
from .board.views import CreateListBoardViewSet
from rest_framework.routers import DefaultRouter
from .auth import views as api_auth_views


router = DefaultRouter()
router.register(r'boards', CreateListBoardViewSet, basename='board')
urlpatterns = router.urls

#authorization
urlpatterns += [
	path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
	path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
	path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
	path("login/", api_auth_views.LoginApiView.as_view(), name="login"),
	]


