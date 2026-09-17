import logging

from asgiref.sync import sync_to_async
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, View
from t_tech.invest.exceptions import RequestError

from user.forms import UserCreatForm
from user.functions import check_and_sync_tinvest_accounts

from .forms import TTokenImportForm
from .models import TInvestAccount

logger = logging.getLogger(__name__)


class SignUpView(CreateView):
    form_class = UserCreatForm
    success_url = reverse_lazy("user:login")
    template_name = "registration/signup.html"


class AsyncTInvestAccountListView(View):
    template_name = "t_invest/account/accounts_list.html"

    async def get(self, request, *args, **kwargs):
        user = await request.auser()
        if not user.is_authenticated:
            messages.error(self.request, "Авторизуйте в системе!")
            return HttpResponseRedirect(reverse("user:login"))
        accounts = []
        async for account in TInvestAccount.objects.filter(user=user).order_by(
            "-created_at"
        ):
            accounts.append(account)
        context = {
            "accounts": accounts,
            "user": user,
        }
        messages.success(self.request, "Обновлен список ваших счетов!")
        response = await sync_to_async(render)(
            request, self.template_name, context
        )
        return response


logger = logging.getLogger(__name__)


class AsyncTInvestAccountCreateView(View):
    template_name = "t_invest/account/create_account_form.html"

    async def get(self, request, *args, **kwargs):
        user = await request.auser()
        if not user.is_authenticated:
            return redirect("user:login")

        form = TTokenImportForm()

        return await sync_to_async(render)(
            request, self.template_name, {"form": form, "user": user}
        )

    async def post(self, request, *args, **kwargs):
        user = await request.auser()
        if not user.is_authenticated:
            return redirect("user:login")

        form = TTokenImportForm(request.POST)

        if form.is_valid():
            token = form.cleaned_data["access_token"]
            try:
                success_report = await check_and_sync_tinvest_accounts(
                    user, token
                )
                messages.success(
                    self.request,
                    f"{success_report}",
                )
                return redirect("user:account_list")

            except ValidationError as e:
                error_msg = (
                    e.message if hasattr(e, "message") else str(e.messages[0])
                )
                form.add_error(None, error_msg)

            except RequestError as e:
                tracking_id = (
                    e.metadata.tracking_id if e.metadata else "UNKNOWN"
                )
                logger.error(
                    "Error tracking_id=%s code=%s", tracking_id, str(e.code)
                )
                form.add_error(
                    None,
                    f"ОШИБКА API Т-ИНВЕСТИЦИЙ: TRACKING_ID={tracking_id} CODE={e.code}",
                )
                messages.success(
                    self.request,
                    f"{e}",
                )

            except Exception as e:
                logger.exception(
                    "Критическая ошибка во View при импорте токена"
                )
                form.add_error(
                    None,
                    f"ПРОИЗОШЛА НЕПРЕДВИДЕННАЯ ОШИБКА. СВЯЗЬ ИЛИ БД: {str(e).upper()}",
                )
        return await sync_to_async(render)(
            request,
            self.template_name,
            {
                "form": form,
                "user": user,
            },
        )
