from django.urls import path
from . import views

app_name = "board"
urlpatterns = [
    path('', views.HomePage.as_view(), name="home"),
]