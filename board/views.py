from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Board

class HomePage(LoginRequiredMixin, TemplateView):
	template_name = "board/home/home.html"

class BoardDetail(LoginRequiredMixin, DetailView):
	template_name = "board/board/main.html"

	def get_queryset(self):
		return Board.objects.filter(owner=self.request.user)