from django.urls import path

from terminal.views import AsyncTerminalMain

app_name = "terminal"

urlpatterns = [
    path("terminal/", AsyncTerminalMain.as_view(), name="terminal"),
]
