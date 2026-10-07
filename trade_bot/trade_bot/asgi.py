import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path

# 1. Установка переменных окружения Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trade_bot.settings")

# 2. Инициализация ASGI-приложения Django (должна происходить ДО импорта консьюмеров!)
django_asgi_app = get_asgi_application()

# 3. Импорт асинхронного потребителя
from data_recipient.consumers import TradingTerminalConsumer

# 4. Общая маршрутизация протоколов
application = ProtocolTypeRouter(
    {
        # Стандартные HTTP запросы (Views, REST API)
        "http": django_asgi_app,
        # Асинхронные WebSocket соединения
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    # Регулярное выражение позволяет принимать любой тикер (SBER, GAZP, VTBR) динамически
                    re_path(
                        r"^ws/trades/(?P<ticker_name>\w+)/$",
                        TradingTerminalConsumer.as_asgi(),
                    ),
                ]
            )
        ),
    }
)
