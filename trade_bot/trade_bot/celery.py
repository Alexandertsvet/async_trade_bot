import os
import logging
from celery import Celery
logger = logging.getLogger(__name__)
# Устанавливаем настройки Django по умолчанию
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trade_bot.settings")

app = Celery("trade_bot")

# Загружаем настройки из Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находим задачи в файлах tasks.py каждого приложения
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    logger.info(f"DEBUG_TASK // Request: {self.request!r}")
