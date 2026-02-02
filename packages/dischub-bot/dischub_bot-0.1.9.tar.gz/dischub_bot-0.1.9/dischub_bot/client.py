import MetaTrader5 as mt5
from .bot_logic import run_bot
from .exceptions import BotException

class DischubBotClient:
    def __init__(self, login: int, password: str, server: str):
        self.login = login
        self.password = password
        self.server = server

    def test_connection(self):
        if not mt5.initialize(
            login=self.login,
            password=self.password,
            server=self.server
        ):
            error = mt5.last_error()
            mt5.shutdown()
            raise BotException(f"MT5 login failed: {error}")

        account = mt5.account_info()
        mt5.shutdown()

        if account is None:
            raise BotException("MT5 connected but account info unavailable")

        is_demo = account.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
        is_live = account.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL

        return account, is_demo, is_live

    def start_bot(self):
        try:
            run_bot(self.login, self.password, self.server)
        except Exception as e:
            raise BotException(f"Bot runtime error: {e}")
