from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView

from account.models import AboutSite, AboutSiteImage, Connection

from .models import Board


class HomePage(TemplateView):
    template_name = "board/home/home.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return redirect("board:landing")
        return super().get(request, *args, **kwargs)


class BoardDetail(LoginRequiredMixin, DetailView):
    template_name = "board/board/main.html"

    def get_queryset(self):
        q = (
            Q(owner=self.request.user) | Q(board_memberships__user=self.request.user)
        ) & Q(closed=False)
        return Board.objects.filter(q).distinct()


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
            ) from None
        return obj


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "board/setting/settings.html"


class LandingPage(TemplateView):
    template_name = "board/landing/landing.html"

    def get(self, request, *args, **kwargs):
        # if request.user.is_authenticated:
        # 	return redirect("board:home")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            dashboard_image = AboutSiteImage.objects.get(title="dashboard")
            setting_notif_image = AboutSiteImage.objects.get(title="setting_notif")
            board_menu_image = AboutSiteImage.objects.get(title="board_menu")
            board_activity_image = AboutSiteImage.objects.get(title="board_activity")
            card_image = AboutSiteImage.objects.get(title="card")
            member_management_image = AboutSiteImage.objects.get(
                title="member_management"
            )
            github = Connection.objects.get(title="github")
            linkedin = Connection.objects.get(title="linkedin")
            email = Connection.objects.get(title="email")
            telegram = Connection.objects.get(title="telegram")
            portfolio = Connection.objects.get(title="portfolio")

            about_site = AboutSite.objects.first()
            print("about_site", about_site)

            context["dashboard_img_url"] = dashboard_image.img.url
            context["setting_notif_img_url"] = setting_notif_image.img.url
            context["board_menu_img_url"] = board_menu_image.img.url
            context["board_activity_img_url"] = board_activity_image.img.url
            context["card_img_url"] = card_image.img.url
            context["member_management_img_url"] = member_management_image.img.url
            context["source_code_url"] = (
                about_site.source_code_page if about_site else ""
            )
            context["celery_task_total_count"] = about_site.celery_task_total_count
            context["test_total_count"] = about_site.test_total_count
            context["model_total_count"] = about_site.model_total_count
            context["api_endpoint_total_count"] = about_site.api_endpoint_total_count

            context["linkedin"] = linkedin.address
            context["github"] = github.address
            context["email"] = email.address
            context["telegram"] = telegram.address
            context["portfolio"] = portfolio.address

        except (AboutSiteImage.DoesNotExist, Connection.DoesNotExist):
            pass

        return context
