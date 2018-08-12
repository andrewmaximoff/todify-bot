import json

import telegram

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse

from TodifyBot.settings import TOKEN, BASE_URL
from .bot import bot


def set_webhook(request):
    s = bot.set_webhook('https://{}/bot/{}'.format(BASE_URL, TOKEN))
    if s:
        return JsonResponse({"msg": "webhook setup ok"})
    else:
        return JsonResponse({"msg": "webhook setup failed"})


@csrf_exempt
def tg_webhook_handler(request):
    if request.method == "POST":
        if request.body:
            update = json.loads(request.body)
            update = telegram.Update.de_json(update, bot)
            bot.dp.process_update(update)
    return HttpResponse('ok')
