import os
import django
from django.core.management import call_command

def init_django_db():
    """
    Initialize Django and apply migrations programmatically.
    Call this at SDK startup.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dischub_bot.settings")
    django.setup()

    # Apply migrations programmatically
    call_command("makemigrations", "dischub_bot", interactive=False)
    call_command("migrate", interactive=False)
