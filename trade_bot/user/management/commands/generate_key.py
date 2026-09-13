from cryptography.fernet import Fernet
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создать секретный ключь"

    def handle(self, *args, **kwargs):
        key = Fernet.generate_key().decode('utf-8')
        self.stdout.write(self.style.SUCCESS(f"{key}"))
        self.stdout.write(self.style.SUCCESS("Ключь успешно создан!"))
