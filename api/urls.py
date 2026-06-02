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
router.register(r'cards', board_views.CardViewSet, basename='card')

router.register(r'checklists', board_views.ChecklistViewSet, basename='checklist')
router.register(r'checklist-items', board_views.ChecklistItemViewSet, basename='checklist_items')
router.register(r'comments', board_views.CommentViewSet, basename='comments')
router.register(r'card-files', board_views.CardFileViewSet, basename='card_file')
router.register(r'card-images', board_views.CardImageViewSet, basename='card_image')
router.register(r'card-labels', board_views.CardLabelViewSet, basename='card_label')
router.register(r'board-lists', board_views.BoardListViewSet, basename='board_list')
router.register(r'card-members', board_views.CardMemberViewSet, basename='card_member')
router.register(r'board-members', board_views.BoardMemberViewSet, basename='board_member')








urlpatterns = router.urls

urlpatterns += [
	path("guest-boards/", board_views.GuestBoardListView.as_view(), name="guest_boards"),
	path("user/", board_views.UserRetrieveView.as_view(), name="user"),
	path("search/board/", board_views.SearchBoardView.as_view(), name="search_boards"),
	path("search/card/", board_views.SearchCardView.as_view(), name="search_cards"),
	path("closed/", board_views.ClosedBoardView.as_view(), name="closed_boards"),

	path("board/<int:pk>/", board_views.BoardRetrieveView.as_view(), name="board"),
	path("card/<int:pk>/", board_views.CardUpdateView.as_view(), name="card_update"),

	path("current-user/", board_views.CurrentUser.as_view(), name="current_user"),
	path("board-list-order/", board_views.BoardListOrderUpdating.as_view(), name="update_list_order"),
	path("card-order/", board_views.CardOrderUpdating.as_view(), name="card_order"),










]

#authorization
urlpatterns += [
	path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
	path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
	path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
	path("login/", api_auth_views.LoginApiView.as_view(), name="login"),
	]


