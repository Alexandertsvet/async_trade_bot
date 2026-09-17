from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    """
    python3 manage.py init_user --username user --email email@mail.ru --password password
    """

    help = "Создает единственного пользователя в системе (Синглтон) на асинхронный лад"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", type=str, required=True, help="Имя пользователя"
        )
        parser.add_argument(
            "--email", type=str, required=True, help="Электронная почта"
        )
        parser.add_argument(
            "--password", type=str, required=True, help="Пароль пользователя"
        )

    def handle(self, *args, **options):
        return async_to_sync(self.handle_async)(*args, **options)

    async def handle_async(self, *args, **options):
        """
        Основная бизнес-логика команды, полностью работающая в async/await.
        """
        username = options["username"]
        email = options["email"]
        password = options["password"]
        if await User.objects.aexists():
            self.stdout.write(
                self.style.WARNING(
                    "Пользователь уже зарегистрирован в системе."
                )
            )
            self.stdout.write(
                self.style.ERROR("Выход из программы без изменений!")
            )
            self.stdout.write(
                self.style.SUCCESS("Перейдите на следующий этап каманда:")
            )
            self.stdout.write(
                self.style.MIGRATE_HEADING("python3 manage.py init_system")
            )
            return

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Проверка возможности создания пользователя..."
            )
        )
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            await user.asave()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно создан единственный пользователь: "{username}" ({email})'
                )
            )
            self.stdout.write(
                self.style.SUCCESS("Перейдите на следующий этап каманда:")
            )
            self.stdout.write(
                self.style.MIGRATE_HEADING("python3 manage.py init_sistem")
            )
        except ValidationError as e:
            raise CommandError(f"Ошибка валидации: {e.messages}")
        except Exception as e:
            raise CommandError(
                f"Непредвиденная ошибка при создании пользователя: {e}"
            )
