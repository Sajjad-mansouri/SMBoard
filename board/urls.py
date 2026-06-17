from django.urls import path
from . import views

app_name = "board"
urlpatterns = [
    path('', views.HomePage.as_view(), name="home"),
    path('landing/', views.LandingPage.as_view(), name="landing"),
    path('board/<int:pk>/', views.BoardDetail.as_view(), name="board_detail"),
    path("public/<str:short_uuid>/<slug:slug>/", views.PublicBoardDetail.as_view(), name="public_board_detail"),
    path('settings/', views.SettingsView.as_view(), name="settings"),




]