from terminal.views import AsyncTerminalMain
from django.urls import path, reverse_lazy

app_name = "terminal"

urlpatterns = [
    path("terminal/", AsyncTerminalMain.as_view(), name="terminal"),
]
