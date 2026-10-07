from asgiref.sync import sync_to_async
from django.shortcuts import render
from django.views.generic import View


class AsyncTerminalMain(View):
    template_name = "terminal/terminal_main.html"

    async def get(self, request, *args, **kwargs):
        user = await request.auser()
        if not user.is_authenticated:
            return redirect("user:login")

        return await sync_to_async(render)(
            request, self.template_name, {"user": user}
        )
