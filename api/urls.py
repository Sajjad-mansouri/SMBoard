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
router.register(r'boards', board_views.BoardViewSet, basename='board')
urlpatterns = router.urls

urlpatterns += [
	path("guest-boards/", board_views.GuestBoardListView.as_view(), name="guest_boards"),
	path("user/", board_views.UserRetrieveView.as_view(), name="user"),
	path("search/board/", board_views.SearchBoardView.as_view(), name="search_boards"),
	path("search/card/", board_views.SearchCardView.as_view(), name="search_cards"),
	path("closed/", board_views.ClosedBoardView.as_view(), name="closed_boards"),

	path("board/<int:pk>", board_views.BoardRetrieveView.as_view(), name="board"),






]

#authorization
urlpatterns += [
	path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
	path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
	path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
	path("login/", api_auth_views.LoginApiView.as_view(), name="login"),
	]


