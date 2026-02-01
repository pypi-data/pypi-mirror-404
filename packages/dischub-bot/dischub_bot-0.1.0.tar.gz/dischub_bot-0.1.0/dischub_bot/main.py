import os
import threading
import time
import webbrowser
import django
from django.core.management import call_command

def start_django_ui():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dischub_bot.settings")
    django.setup()

    threading.Thread(
        target=lambda: (
            time.sleep(1),
            webbrowser.open("http://127.0.0.1:8000/")
        ),
        daemon=True
    ).start()

    call_command("runserver", "8000")

if __name__ == "__main__":
    start_django_ui()
