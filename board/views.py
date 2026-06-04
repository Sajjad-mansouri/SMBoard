from django.shortcuts import render
from django.http import Http404
from django.utils.translation import gettext as _
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

class PublicBoardDetail(DetailView):
	template_name = "board/board/public.html"

	def get_queryset(self):
		return Board.objects.filter(status="public")

	def get_object(self, queryset=None):
		short_uuid = self.kwargs.get("short_uuid")
		slug = self.kwargs.get("slug")
		if queryset is None:
			queryset = self.get_queryset()
		queryset = queryset.filter(short_uuid=short_uuid, slug=slug)
		try:
			# Get the single item from the filtered queryset
			obj = queryset.get()
		except queryset.model.DoesNotExist:
			raise Http404(
				_("No %(verbose_name)s found matching the query")
				% {"verbose_name": queryset.model._meta.verbose_name}
			)
		return obj