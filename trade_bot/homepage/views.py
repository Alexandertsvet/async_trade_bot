from django.contrib.auth import get_user_model
from django.shortcuts import render

User = get_user_model()


def home_view(request):
    total_traders = User.objects.acount()
    api_status = "ONLINE"

    context = {
        "total_traders": total_traders,
        "api_status": api_status,
        "bot_version": "6.1.0-beta",
    }

    return render(request, "homepage/home.html", context)
