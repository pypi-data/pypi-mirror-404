from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("guidelines/", views.guidelines_view, name="guidelines"),
    path("manage/bot/", views.manage_bot_view, name="manage_bot"),
    path("account/login/view/", views.account_login_view, name="account_login_view"),
    path("subscribe/", views.subscribe_view, name="subscribe"),
    path("verify/payment/", views.verify_payment_view, name="verify_payment"),
    path("save/symbol/settings/", views.save_symbol_settings, name="save_symbol_settings"),
    path("stop/bot/", views.stop_bot_view, name="stop_bot"),
    path("logout/user/", views.logout_user_view, name="logout_user"),
]
