from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .views import SignUpView

app_name = "user"

urlpatterns = [
    path("user/signup/", SignUpView.as_view(), name="signup"),
    path(
        "user/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("user/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "user/password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            success_url=reverse_lazy("user:password_reset_done"),
            # email_template_name='registration/password_reset_email.html'
            email_template_name="registration/password_reset_email.txt",
        ),
        name="password_reset",
    ),
    path(
        "user/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "user/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("user:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "user/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "user/password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html",
            success_url=reverse_lazy("user:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "user/password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),
]
