from django.urls import path

from TodifyBot.settings import TOKEN
from .apps import BotConfig
from .views import (
    set_webhook,
    tg_webhook_handler
)


app_name = BotConfig.name
urlpatterns = [
    path(f'{TOKEN}', tg_webhook_handler, name='tg-webhook-handler'),
    path('set_webhook/', set_webhook, name='set-webhook'),
]
