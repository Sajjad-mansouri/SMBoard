from django.urls import path, include
from . import views

app_name = "account"

urlpatterns = [
	path("register/<uidb64>/<token>/", views.RegistrationConfirmView.as_view(), name="register-confirm"),
	path("register/", views.RegistrationView.as_view(), name="register"),
	path("register/registration_done/", views.RegistrationDoneView.as_view(), name="registration_done"),

	path("login/", views.LoginView.as_view(), name="login"),

	path("password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]