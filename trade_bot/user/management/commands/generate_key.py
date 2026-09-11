from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key
from cryptography.fernet import Fernet


class Command(BaseCommand):
    help = "Создать секретный ключь"

    def handle(self, *args, **kwargs):
        key = Fernet.generate_key().decode('utf-8')
        self.stdout.write(self.style.SUCCESS(f"{key}"))
        self.stdout.write(self.style.SUCCESS("Ключь успешно создан!"))