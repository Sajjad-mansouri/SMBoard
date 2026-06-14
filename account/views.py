from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import views as auth_views
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Profile, Notification
from . import forms

UserModel = get_user_model()
INTERNAL_REGISTRATION_SESSION_TOKEN = "_registration_token"

class PasswordContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"title": self.title, "subtitle": None, **(self.extra_context or {})}
        )
        return context

class RegistrationView(CreateView):
    email_template_name = "account/registration/registration_email.html"
    extra_email_context = None
    response_type = "JSON"
    form_class = forms.UserRegistrationForm
    from_email = None
    html_email_template_name = None
    subject_template_name = "account/registration/registration_subject.txt"
    success_url = reverse_lazy("account:registration_done")
    template_name = "account/registration/register.html"
    title = _("Register")
    token_generator = default_token_generator

    def form_valid(self, form):
        opts = {
            "use_https": self.request.is_secure(),
            "token_generator": self.token_generator,
            "from_email": self.from_email,
            "email_template_name": self.email_template_name,
            "subject_template_name": self.subject_template_name,
            "request": self.request,
            "html_email_template_name": self.html_email_template_name,
            "extra_email_context": self.extra_email_context,
        }
        form.save(**opts)
        self.request.session["email"] = form.cleaned_data["email"]
        if self.response_type == "JSON":
            return JsonResponse({"status":True})
        return super().form_valid(form)

    def form_invalid(self, form):

        if self.response_type == "JSON":
            errors = form.errors.get_json_data()
            return JsonResponse({"status":False, "errors":errors})

        return super().form_invalid(form)



class RegistrationDoneView(PasswordContextMixin, TemplateView):
    template_name = "account/registration/registration_done.html"
    title = _("Activition Email sent")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get("email")
        return context


@method_decorator(login_not_required, name="dispatch")
class RegistrationConfirmView(PasswordContextMixin, TemplateView):
    template_name = 'account/registration/registration_complete.html'
    token_generator = default_token_generator
    title = "registration complete"
    confirm_registration_url_token = "confirm-registration"

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):

        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])
       
        if self.user is not None:
            token = kwargs["token"]
            if token == self.confirm_registration_url_token:
                session_token = self.request.session.get(INTERNAL_REGISTRATION_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    self.validlink=True
                    self.user.is_active=True
                    self.user.save()
                    Profile.objects.create(user=self.user)
                    Notification.objects.create(user=self.user)
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_REGISTRATION_SESSION_TOKEN] = token

                    redirect_url = self.request.path.replace(
                        token, self.confirm_registration_url_token
                    )
                    return HttpResponseRedirect(redirect_url)

        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())



    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            pk = UserModel._meta.pk.to_python(uid)
            user = UserModel._default_manager.get(pk=pk)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UserModel.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context["validlink"] = True
        else:
            context.update(
                {

                    "title": _("Password reset unsuccessful"),
                    "validlink": False,
                }
            )
        return context


class LoginView(auth_views.LoginView):
    template_name = "account/registration/login.html"




class PasswordResetView(auth_views. PasswordResetView):
    template_name = "account/registration/pass_reset_form.html"
    email_template_name = "account/registration/pass_reset_email.html"
    subject_template_name = "account/registration/pass_reset_subject.txt"
    success_url = reverse_lazy("account:password_reset_done")



class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "account/registration/pass_reset_done.html"

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "account/registration/pass_reset_confirm.html"
    success_url = reverse_lazy("account:password_reset_complete")

class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "account/registration/pass_reset_complete.html"