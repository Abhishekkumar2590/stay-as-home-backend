import os
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def ensure_superuser(sender, **kwargs):
    """
    Creates an initial superuser only if no superuser exists in the database.
    Does NOT overwrite or reset any existing user passwords.
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD') or os.environ.get('ADMIN_PASSWORD')
            admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@quickstay.com')
            if admin_password:
                User.objects.create_superuser(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )
    except Exception:
        pass

class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'

    def ready(self):
        post_migrate.connect(ensure_superuser, sender=self)
