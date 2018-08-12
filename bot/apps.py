import logging

from django.apps import AppConfig

from .bot import bot
from TodifyBot.settings import BASE_URL, TOKEN

logger = logging.getLogger(__name__)


class BotConfig(AppConfig):
    name = 'bot'

    def ready(self):
        s = bot.set_webhook('https://{}/bot/{}'.format(BASE_URL, TOKEN))
        if s:
            logger.info('webhook setup ok')
        else:
            logger.error('webhook setup failed')
