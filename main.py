import telegram
import logging
from telegram.ext import Updater, CommandHandler


class Bot:
    def __init__(self):
        self.token = ''  # Here's the Telegram API
        self.bot = telegram.Bot(token=self.token)
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.define_commands()
        self.start_bot()

    def start_bot(self):
        self.updater.start_polling()

    def stop_bot(self):
        self.updater.stop()

    def define_commands(self):
        # ~~~~~~~~~~~~~~~~ COMMANDS ~~~~~~~~~~~~~~~~~~
        start_handler = CommandHandler('start', self.start)
        # ~~~~~~~~~~~~~~~~ HANDLER ~~~~~~~~~~~~~~~~~~~
        self.dispatcher.add_handler(start_handler)

    def start(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
