from django.urls import path
from rest_framework_simplejwt.views import (
		TokenObtainPairView,
		TokenRefreshView,
		TokenVerifyView
	)
from .board import views as board_views
from rest_framework.routers import DefaultRouter
from .auth import views as api_auth_views



router = DefaultRouter()
router.register(r'boards', board_views.CreateListBoardViewSet, basename='board')
urlpatterns = router.urls

urlpatterns += [
	path("guest-boards/", board_views.GuestBoardListView.as_view(), name="guest_boards"),

]

#authorization
urlpatterns += [
	path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
	path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
	path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
	path("login/", api_auth_views.LoginApiView.as_view(), name="login"),
	]


