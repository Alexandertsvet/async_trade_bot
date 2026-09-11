from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.shortcuts import render

User = get_user_model()
async_render = sync_to_async(render)


async def home_view(request):
    total_traders = await User.objects.acount()
    api_status = "ONLINE"

    context = {
        "total_traders": total_traders,
        "api_status": api_status,
        "bot_version": "0.0.0-beta",
    }
    return await async_render(request, "homepage/home.html", context)
