from django.urls import path
from . import views

app_name = "board"
urlpatterns = [
    path('', views.HomePage.as_view(), name="home"),
    path('board/<int:pk>/', views.BoardDetail.as_view(), name="board_detail"),

]