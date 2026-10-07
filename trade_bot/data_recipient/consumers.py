# t_tech/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class TradingTerminalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        # Проверка авторизации
        if not self.user.is_authenticated:
            logger.warning("WS//REJECTED//UNAUTHENTICATED_USER")
            await self.close()
            return

        # Извлекаем тикер из URL (например, из /ws/trades/sber/ получим 'sber')
        self.ticker_name = self.scope["url_route"]["kwargs"]["ticker_name"].upper()

        # Имя группы рассылки рыночных данных (совпадает с t_get_data)
        self.broadcast_group = "market_data_broadcast"

        # При подключении подписываем клиента на поток
        await self.channel_layer.group_add(
            self.broadcast_group,
            self.channel_name
        )
        await self.accept()
        # Информативный лог: теперь мы видим, какую именно акцию открыл пользователь
        logger.info(f"WS//CONNECTED//USER: {self.user.username.upper()}//WATCHING: {self.ticker_name}")

    async def disconnect(self, close_code):
        if hasattr(self, 'broadcast_group'):
            await self.channel_layer.group_discard(
                self.broadcast_group,
                self.channel_name
            )
        logger.info(f"WS//DISCONNECTED//CODE: {close_code}")

    async def stream_market_data(self, event):
        """Прямая отправка сырой JSON-строки фронтенду"""
        await self.send(text_data=event["content"])
