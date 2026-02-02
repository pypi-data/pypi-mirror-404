from . models import SymbolSettings, PaymentVerification
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from datetime import timedelta

############################################ Context Processors #############################################

def symbol_settings(request):
    try:
        symbol = SymbolSettings.objects.filter().last()
    except ObjectDoesNotExist:
        symbol = None
    except Exception as e:
        symbol = None
    return {
        'symbol': symbol,
        }

def subsciption_status_check(request):
    subscription = PaymentVerification.objects.last()
    subscription_status = {
        "valid": False,
        "message": "No subscription"
    }
    if subscription:
        now = timezone.now()
        if now <= subscription.paid_at + timedelta(days=1):
            subscription_status["valid"] = True
            subscription_status["message"] = "Subscription valid"
        else:
            SymbolSettings.objects.all().delete()
            subscription_status["message"] = "Subscription expired"
    return  {
        "subscription_status": subscription_status
    }

def alerts_messages(request):
    return  {
    }