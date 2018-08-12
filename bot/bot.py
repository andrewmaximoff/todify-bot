import logging

from queue import Queue

import emoji
import telegram

from telegram import (
    Bot,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    RegexHandler,
    Dispatcher,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
)

from TodifyBot.settings import TOKEN
from .models import Person, Task
from .utils import (
    Singleton,
)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


COMMANDS, SETTINGS, CHOOSING_LANGUAGE, TITLE_TASK, DESCRIPTION_TASK, TASK_LIST, CHOOSING_TASK = range(7)


###############
#    Emoji    #
###############

emoji_not_done = emoji.emojize(':heavy_minus_sign:')
emoji_done = emoji.emojize(':heavy_check_mark:')
emoji_delete = emoji.emojize(':heavy_multiplication_x:')
emoji_return = emoji.emojize(':heavy_minus_sign:')

###############
#  Keyboards  #
###############

# Commands keyboard
commands_keyboard = [['New task', 'Task list'],
                     ['Settings']]
commands_markup = ReplyKeyboardMarkup(commands_keyboard, resize_keyboard=True)


# Language keyboard
languages = {
    'EN': b'\xF0\x9F\x87\xAC\xF0\x9F\x87\xA7'.decode('utf-8'),
    'RU': b'\xF0\x9F\x87\xB7\xF0\x9F\x87\xBA'.decode('utf-8'),
}
language_keyboard = [
    [InlineKeyboardButton(emoji, callback_data=code) for code, emoji in languages.items()]
]
language_markup = InlineKeyboardMarkup(language_keyboard)


# Settings keyboard
settings_keyboard = [
    ['Language'],
    ['Back'],
]
settings_markup = ReplyKeyboardMarkup(settings_keyboard, resize_keyboard=True)


# Back keyboard
back_keyboard = [
    ['Back']
]
back_markup = ReplyKeyboardMarkup(back_keyboard,  resize_keyboard=True)


# Cancel keyboard
cancel_keyboard = [
    ['Cancel']
]
cancel_markup = ReplyKeyboardMarkup(cancel_keyboard,  resize_keyboard=True)


class TodifyBot(Bot):
    __metaclass__ = Singleton

    def __init__(self, token):
        super().__init__(token)
        update_queue = Queue()
        self.dp = Dispatcher(self, update_queue)
        self.add_update_handlers()

    def add_update_handlers(self):
        """TODO: add doc string
        """
        # self.dp.add_handler(CommandHandler("start", self._start))
        self.dp.add_handler(self.conv_handler())
        # self.dp.add_handler(CallbackQueryHandler(self._choose_lang))
        self.dp.add_handler(CommandHandler("help", self._help))
        # self.dp.add_handler(CommandHandler("test", self._test))

    def _start(self, _: str, update: telegram.Update):
        """Add a new user to the database.
        Handler for the /set <group> command
        Args:
            _: This object represents a Telegram Bot.
            update: Incoming telegram update.
        """
        user_id = str(update.message.from_user['id'])
        Person.objects.get_or_create(user_id=user_id)
        self.send_message(
            update.message.chat_id,
            text='Hello!',
            reply_markup=ReplyKeyboardRemove()
        )
        self.send_message(
            update.message.chat_id,
            text='Choose your language:(Ru not implemented)',
            reply_markup=language_markup
        )
        return CHOOSING_LANGUAGE

    def _help(self, _: str, update: telegram.Update):
        """Send help message.
        Handler for the /help command

        Args:
            _ : This object represents a Telegram Bot.
            update: Incoming telegram update.
        """
        self.send_message(
            update.message.chat_id,
            text='Help message',
            parse_mode='Markdown'
        )

    def _test(self, _: str, update: telegram.Update):
        self.send_message(
            update.message.chat_id,
            text='{}'.format(update.message.from_user['id']),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )

    def _choose_lang(self, _, update):
        query = update.callback_query
        user_id = str(update.callback_query.from_user['id'])

        user, _ = Person.objects.get_or_create(user_id=user_id)
        user.language = query.data
        user.save()
        self.edit_message_text(
            text="Selected language: {}".format(languages.get(query.data)),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        self.send_message(
            text="What's next?",
            chat_id=query.message.chat_id,
            reply_markup=commands_markup
        )
        return COMMANDS

    def _new_task(self, _, update):
        self.send_message(
            update.message.chat_id,
            text="Name task:",
            reply_markup=cancel_markup
        )
        return TITLE_TASK

    def _mark_task(self, _, update):
        self.send_message(
            update.message.chat_id,
            text="Name task:",
            reply_markup=cancel_markup
        )
        return TITLE_TASK

    def _task_details(self, _, update):
        query = update.callback_query
        task = Task.objects.get(pk=query.data)
        task_details_keyboard = [
            [InlineKeyboardButton(emoji_done, callback_data=f'{task.pk}:done')
             if not task.done else
             InlineKeyboardButton(emoji_return, callback_data=f'{task.pk}:return'),
             InlineKeyboardButton(emoji_delete, callback_data=f'{task.pk}:delete')]
        ]
        task_details_markup = InlineKeyboardMarkup(task_details_keyboard)

        self.edit_message_text(
            text=f'*{task.title}* {emoji_done if task.done else emoji_not_done}\n'
                 f'{task.description}',
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=task_details_markup,
            parse_mode='Markdown',
        )
        return CHOOSING_TASK

    def _task_list(self, _, update):
        user_id = str(update.message.from_user['id'])
        tasks = Task.objects.filter(owner__user_id=user_id)
        tasks_keyboard = [
            [
                InlineKeyboardButton(
                    f'{task.title} {emoji_done if task.done else emoji_not_done}',
                    callback_data=task.pk
                )
            ] for task in tasks
        ]
        tasks_markup = InlineKeyboardMarkup(tasks_keyboard)
        self.send_message(
            update.message.chat_id,
            text=f"Your tasks:",
            parse_mode='Markdown',
            reply_markup=tasks_markup,
        )
        return COMMANDS

    def _task_actions(self, _, update):
        query = update.callback_query
        task_pk, task_actions = query.data.split(':')
        task = Task.objects.get(pk=task_pk)
        if task_actions == 'done':
            task.done = True
            task.save()
        elif task_actions == 'delete':
            task.delete()
        elif task_actions == 'return':
            task.done = False
            task.save()

        user_id = str(update.callback_query.from_user['id'])
        tasks = Task.objects.filter(owner__user_id=user_id)
        tasks_keyboard = [
            [
                InlineKeyboardButton(
                    f'{task.title} {emoji_done if task.done else emoji_not_done}',
                    callback_data=task.pk
                )
            ] for task in tasks
        ]
        tasks_markup = InlineKeyboardMarkup(tasks_keyboard)
        self.edit_message_text(
            text=f"Your tasks:",
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            parse_mode='Markdown',
            reply_markup=tasks_markup,
        )
        return COMMANDS

    def _settings(self,  _, update):
        user_id = str(update.message.from_user['id'])
        user, _ = Person.objects.get_or_create(user_id=user_id)
        lang = user.language

        self.send_message(
            update.message.chat_id,
            text=f"Your settings:\n\nLanguage: {languages.get(lang)}",
            reply_markup=settings_markup,
            parse_mode='Markdown',
        )
        return SETTINGS

    def _create_task_title(self, _, update, user_data):
        title = update.message.text
        user_data['title'] = title
        self.send_message(
            update.message.chat_id,
            text="Task description:",
            reply_markup=cancel_markup
        )
        return DESCRIPTION_TASK

    def _create_task_description(self, _, update, user_data):
        title = user_data['title']
        description = update.message.text
        user_id = str(update.message.from_user['id'])
        user, _ = Person.objects.get_or_create(user_id=user_id)
        Task.create(title, description, user)
        self.send_message(
            update.message.chat_id,
            text="*Task created!*",
            reply_markup=commands_markup,
            parse_mode='Markdown'
        )
        self._task_list(_, update)
        return COMMANDS

    def _cancel(self, _, update):
        self.send_message(
            text="No problem.\nWhat's next?",
            chat_id=update.message.chat_id,
            reply_markup=commands_markup
        )
        return COMMANDS

    def _choice_lang(self, _: str, update: telegram.Update):
        user_id = str(update.message.from_user['id'])
        Person.objects.get_or_create(user_id=user_id)

        self.send_message(
            chat_id=update.message.chat_id,
            text='Choose your language:',
            reply_markup=language_markup
        )
        return SETTINGS

    def conv_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler('start', self._start)],

            states={
                COMMANDS: [
                    CallbackQueryHandler(self._task_details),
                    RegexHandler('^New task$',
                                 self._new_task),
                    RegexHandler('^Task list$',
                                 self._task_list),
                    RegexHandler('^Settings$',
                                 self._settings),
                ],
                CHOOSING_LANGUAGE: [
                    CallbackQueryHandler(self._choose_lang),
                    RegexHandler('^Back$', self._cancel),
                ],
                SETTINGS: [
                    CallbackQueryHandler(self._choose_lang),
                    RegexHandler('^Language$', self._choice_lang),
                    RegexHandler('^Back$', self._cancel),
                ],
                TITLE_TASK: [
                    RegexHandler('^Cancel$', self._cancel),
                    MessageHandler(Filters.text, self._create_task_title, pass_user_data=True)
                ],
                DESCRIPTION_TASK: [
                    RegexHandler('^Cancel$', self._cancel),
                    MessageHandler(Filters.text, self._create_task_description, pass_user_data=True)
                ],
                CHOOSING_TASK: [

                    CallbackQueryHandler(self._task_actions),
                    RegexHandler('^New task$',
                                 self._new_task),
                    RegexHandler('^Task list$',
                                 self._task_list),
                    RegexHandler('^Settings$',
                                 self._settings),
                ]
            },

            fallbacks=[CommandHandler("test", self._test)],
            allow_reentry=True
        )


bot = TodifyBot(TOKEN)
