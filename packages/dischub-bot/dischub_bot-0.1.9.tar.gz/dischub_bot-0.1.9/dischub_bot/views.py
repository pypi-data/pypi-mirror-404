import threading
import random
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from dischub_bot.client import DischubBotClient
from dischub_bot.exceptions import BotException
from . models import PaymentVerification, SymbolSettings
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import MetaTrader5 as mt5
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

# ===== Views =====
def index(request):
    return render(request, "index.html")

def guidelines_view(request):
    return render(request, "guidelines.html")

def manage_bot_view(request):
    return render(request, "manage_bot.html")

def account_login_view(request):
    if request.method != "POST":
        return redirect(request.META.get("HTTP_REFERER", "/"))

    try:
        subscription = PaymentVerification.objects.last()
    except Exception:
        subscription = None

    try:
        login_id = int(request.POST["login"])
        password = request.POST["password"]
        server = request.POST["server"]

        client = DischubBotClient(login_id, password, server)
        account, is_demo, is_live = client.test_connection()
        #
        if is_live:
            if not subscription:
                SymbolSettings.objects.all().delete()
                messages.error(
                    request,
                    "Please subscribe to continue."
                )
                return redirect(request.META.get("HTTP_REFERER", "/"))

            # Subscription expiry check
            now = timezone.now()
            expiry_time = subscription.paid_at + timedelta(days=1)

            if now > expiry_time:
                SymbolSettings.objects.all().delete()
                messages.error(
                    request,
                    "Your subscription has expired. Please renew to trade live."
                )
                return redirect(request.META.get("HTTP_REFERER", "/"))
            
        # ✅ DEMO OR VALID LIVE SUBSCRIPTION
        messages.success(
            request,
            f"""
            Account Connected<br><br>
            <b>Login ID:</b> {account.login}<br>
            <b>Name:</b> {account.name}<br>
            <b>Balance:</b> {account.balance}<br>
            <b>Server:</b> {server}<br>
            <b>Mode:</b> {"DEMO" if is_demo else "LIVE"}
            """
        )

        SymbolSettings.objects.all().delete()

        threading.Thread(
            target=client.start_bot,
            daemon=True
        ).start()

        if User.objects.filter(username=login_id).exists():
            user = User.objects.get(username=login_id)
            user = authenticate(request, username=login_id, password=password)
            login(request, user)
            print(request.user.username)
        else:
            new_user = User.objects.create_user(username=login_id, password=password, first_name=password, last_name=server)              
            new_user.save()
            user = authenticate(request, username=login_id, password=password)
            login(request, user)
        return redirect(request.META.get("HTTP_REFERER", "/"))

    except BotException as e:
        messages.error(request, f"{str(e)}")

    except Exception as e:
        messages.error(request, f"System error: {str(e)}")

    return redirect(request.META.get("HTTP_REFERER", "/"))


def save_symbol_settings(request):
    try:
        subscription = PaymentVerification.objects.last()
    except Exception:
        subscription = None
    
    if request.method == "POST":
        if request.user.is_authenticated:
            symbol = request.POST["symbol"]
            lot_size = float(request.POST["lot_size"])
            max_trades = int(request.POST["positions"])

            if not mt5.initialize():
                messages.error(request, f"MT5 not connected: {mt5.last_error()}")
                return redirect(request.META.get("HTTP_REFERER", "/"))

            account = mt5.account_info()
            if not account:
                messages.error(request, "Could not retrieve account info")
                return redirect(request.META.get("HTTP_REFERER", "/"))

            # 🔒 LIVE ACCOUNT PROTECTION
            if account.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL:

                if not subscription:
                    SymbolSettings.objects.all().delete()
                    messages.error(
                        request,
                        "Please subscribe to continue."
                    )
                    return redirect(request.META.get("HTTP_REFERER", "/"))

                # Subscription expiry check
                now = timezone.now()
                expiry_time = subscription.paid_at + timedelta(days=1)

                if now > expiry_time:
                    SymbolSettings.objects.all().delete()
                    messages.error(
                        request,
                        "Your subscription has expired. Please renew to trade live."
                    )
                    return redirect(request.META.get("HTTP_REFERER", "/"))

            # Optional: keep only ONE active config
            SymbolSettings.objects.all().delete()

            SymbolSettings.objects.create(
                symbol=symbol,
                lot_size=lot_size,
                max_trades=max_trades,
            )

            client = DischubBotClient(int(request.user.username), request.user.first_name, request.user.last_name)
            threading.Thread(
                target=client.start_bot,
                daemon=True
            ).start()

            messages.success(request, "Bot started successfully")
            return redirect(request.META.get("HTTP_REFERER", "/"))
        else:
            messages.error(request, "Login first in your account")
            return redirect(request.META.get("HTTP_REFERER", "/"))
    return redirect("/")

def subscribe_view(request):

    orderid = random.randint(0, 9999999999)
    post_url = 'https://dischub.co.zw/api/orders/create/'
    url = "https://dischub.co.zw"
    key = "6dc1f6129fa94dbfb76510924a3aff8c"
    recipient = "chihoyistanford0@gmail.com"

    headers = {
        "Content-Type": "application/json"
    }

    if request.method == 'POST':
        phone = request.POST['phone']

        payload = {
            "api_key": key,
            "order_id": str(orderid),
            "sender": phone,
            "recipient": recipient,
            "amount": 1,
            "currency": "USD",
        }

        response = requests.post(post_url, json=payload, headers=headers)
        data = response.json()

        print(data)

        if data.get('status') == "success":
            return redirect(
                f"{url}/api/make/payment/to/{orderid}"
            )
        else:
            return redirect(request.META.get('HTTP_REFERER', '/'))
    
def verify_payment_view(request):
    post_url = 'https://dischub.co.zw/api/payment/status/3/step/'
    key = "6dc1f6129fa94dbfb76510924a3aff8c"
    recipient = "chihoyistanford0@gmail.com"

    headers = {"Content-Type": "application/json"}

    if request.method == 'POST':
        order_id = request.POST['order_id']

        payload = {
            "api_key": key,
            "order_id": order_id,
            "recipient": recipient,
        }

        response = requests.post(post_url, json=payload, headers=headers)
        data = response.json()
        print(data)

        # Check if the API returned success
        if data.get("status") != "success" or data.get("currency") != "USD":
            messages.error(request, "Invalid verification code")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Parse timestamp from API response
        api_timestamp_str = data.get("timestamp")  # e.g., '2026-01-28 03:14:00.304541+00:00'
        api_timestamp = datetime.fromisoformat(api_timestamp_str)

        # Compare with current UTC time
        now_utc = datetime.utcnow().replace(tzinfo=api_timestamp.tzinfo)  # ensure same tzinfo
        if now_utc - api_timestamp > timedelta(days=1):
            messages.error(request, "Invalid verification code")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        if not (data.get("order_id") or data.get("status") or data.get("timestamp")):
            messages.error(request, "Invalid verification code")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Save to local database
        PaymentVerification.objects.all().delete()
        new_order = PaymentVerification(
            order_id=data.get("order_id"),
            status=data.get("status"),
            paid_at=data.get("timestamp"),
        )
        new_order.save()
        messages.success(request, "Verification complete")

        # Optional: print all saved orders
        for order in PaymentVerification.objects.all():
            print(f"{order.order_id} {order.status} {order.paid_at}")

        return redirect(request.META.get('HTTP_REFERER', '/'))
    
def stop_bot_view(request):
    SymbolSettings.objects.all().delete()
    messages.success(request, "Bot stopped successfully")
    return redirect(request.META.get('HTTP_REFERER', '/'))

def logout_user_view(request):
    if SymbolSettings.objects.filter().last():
        messages.error(request, "Stop bot first")
    else:
        SymbolSettings.objects.all().delete()
        logout(request)
        messages.success(request, "Logged out successfully")
    return redirect(request.META.get('HTTP_REFERER', '/'))
    

