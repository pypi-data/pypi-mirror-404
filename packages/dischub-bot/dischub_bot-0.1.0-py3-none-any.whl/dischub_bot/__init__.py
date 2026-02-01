from .main import start_django_ui
from .db import init_django_db

def launch_bot_ui():
    # Ensure database is ready
    init_django_db()
    """
    Call this to open a Django-based local web page
    to input broker credentials and start the bot.
    """
    start_django_ui()
