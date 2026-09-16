from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates or updates a Django superuser password'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'))
        parser.add_argument('--password', type=str, default=os.getenv('DJANGO_SUPERUSER_PASSWORD') or os.getenv('ADMIN_PASSWORD', ''))
        parser.add_argument('--email', type=str, default=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@quickstay.com'))

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if not password:
            self.stdout.write(self.style.WARNING("No password specified. Run with: python manage.py reset_admin --password <your_password>"))
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        action = "Created" if created else "Updated password for"
        self.stdout.write(self.style.SUCCESS(
            f"Successfully {action} superuser '{username}'."
        ))

