import os
import threading
import time
import webbrowser
import django
from django.core.management import call_command

def open_browser():
    time.sleep(1)  # give Django server a moment to start
    webbrowser.open("http://127.0.0.1:8000/")

def start_django_ui():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dischub_bot.settings")
    django.setup()

    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Django server
    call_command("runserver", "8000")

if __name__ == "__main__":
    start_django_ui()

