from django.urls import reverse_lazy
from django.views.generic import CreateView

from user.forms import UserCreatForm


class SignUpView(CreateView):
    form_class = UserCreatForm
    success_url = reverse_lazy("user:login")
    template_name = "registration/signup.html"
