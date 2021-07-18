import telegram
import logging
import requests
import logging
import os
from telegram.ext.callbackcontext import CallbackContext
from toml import load, dump
from bs4 import BeautifulSoup
from telegramtoken import mytoken
from telegram.ext import Updater, CommandHandler, ChatMemberHandler
from typing import Tuple, Optional


class Bot:
    def __init__(self, token):
        self.create_telegramtoken_file()
        self.token = token  # Here's the Telegram API
        self.bot = telegram.Bot(token=self.token)
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.define_commands()
        self.start_bot()
        # self.updater.idle()

    def start_bot(self):
        self.updater.start_polling()

    def stop_bot(self):
        self.updater.stop()

    def define_commands(self):
        # ~~~~~~~~~~~~~~~~ COMMANDS ~~~~~~~~~~~~~~~~~~
        start_handler = CommandHandler('start', self.start)
        track_chats = ChatMemberHandler(
            self.track_chats, ChatMemberHandler.CHAT_MEMBER)
        # ~~~~~~~~~~~~~~~~ HANDLER ~~~~~~~~~~~~~~~~~~~
        self.dispatcher.add_handler(start_handler)
        self.dispatcher.add_handler(track_chats)

    def start(self, update, context):
        """ Sends a message when the command /start is issued. """
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="This is NeeggaSpider, the spider bot for UniTO telegram groups")

    def create_group_list(self, link):
        """
        Given a Simplenote link (like https://app.simplenote.com/p/MRlJ5H), it retrieves every telegram group link in it
        and returns a list containing all the group links.

        Example telegram group link to search for: http://t.me/GreenSaver/
        Example link not to append to the list: https://www.facebook.com/groups/dipinfosupp/
        """
        # ~~~~~~~~~~~~~~~~~ GETTING THE PARSER ~~~~~~~~~~~~~~~~~~~
        page = requests.get(link)
        soup = BeautifulSoup(page.content, 'html.parser')
        # ~~~~~~~~~~~~~~~~~ GETTING THE LINKS ~~~~~~~~~~~~~~~~~~~~
        links = []
        for link in soup.find_all('a'):
            if link.get('href') is not None:
                if link.get('href').startswith('https://t.me/'):
                    links.append(link.get('href'))
        return links

    def create_telegramtoken_file(self):
        """
        If it's not present, it creates the telegramtoken.py
        file and asks for the token from the terminal input
        """
        if not os.path.isfile('telegramtoken.py'):
            with open('telegramtoken.py', 'w') as f:
                f.write('token = "')
                f.write(input("Please enter your telegram token: "))
                f.write('"')
        else:
            print("Token already exists, starting the bot")

    def is_group(self, link: str):
        """
        Given a link, it returns True if it's a telegram group link, False otherwise
        Telegram private chats or bots are not to be considered as groups
        """
        page = requests.get(link)
        soup = BeautifulSoup(page.content, 'html.parser')
        for link in soup.find_all('a'):
            if link.get('href') is not None:
                if link.get('href').startswith('tg://join?'):
                    return True
        return False

    def extract_status_change(self, chat_member_update: telegram.ChatMemberUpdated,) -> Optional[Tuple[bool, bool]]:
        """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
        of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
        the status didn't change.
        """
        status_change = chat_member_update.difference().get("status")
        old_is_member, new_is_member = chat_member_update.difference().get("is_member",
                                                                           (None, None))

        if status_change is None:
            return None

        old_status, new_status = status_change
        was_member = (
            old_status
            in [
                telegram.ChatMember.MEMBER,
                telegram.ChatMember.CREATOR,
                telegram.ChatMember.ADMINISTRATOR,
            ]
            or (old_status == telegram.ChatMember.RESTRICTED and old_is_member is True)
        )
        is_member = (
            new_status
            in [
                telegram.ChatMember.MEMBER,
                telegram.ChatMember.CREATOR,
                telegram.ChatMember.ADMINISTRATOR,
            ]
            or (new_status == telegram.ChatMember.RESTRICTED and new_is_member is True)
        )

        return was_member, is_member

    def track_chats(self, update: telegram.Update, context: CallbackContext) -> None:
        """Tracks the chats the bot is in."""
        result = self.extract_status_change(update.my_chat_member)
        if result is None:
            return
        was_member, is_member = result

        # Let's check who is responsible for the change
        cause_name = update.effective_user.full_name

        # Handle chat types differently:
        chat = update.effective_chat
        if chat.type == telegram.Chat.PRIVATE:
            if not was_member and is_member:
                logger.info("%s started the bot", cause_name)
                context.bot_data.setdefault("user_ids", set()).add(chat.id)
            elif was_member and not is_member:
                logger.info("%s blocked the bot", cause_name)
                context.bot_data.setdefault("user_ids", set()).discard(chat.id)
        elif chat.type in [telegram.Chat.GROUP, telegram.Chat.SUPERGROUP]:
            if not was_member and is_member:
                logger.info("%s added the bot to the group %s",
                            cause_name, chat.title)
                context.bot_data.setdefault("group_ids", set()).add(chat.id)
            elif was_member and not is_member:
                logger.info("%s removed the bot from the group %s",
                            cause_name, chat.title)
                context.bot_data.setdefault(
                    "group_ids", set()).discard(chat.id)
        else:
            if not was_member and is_member:
                logger.info("%s added the bot to the channel %s",
                            cause_name, chat.title)
                context.bot_data.setdefault("channel_ids", set()).add(chat.id)
            elif was_member and not is_member:
                logger.info("%s removed the bot from the channel %s",
                            cause_name, chat.title)
                context.bot_data.setdefault(
                    "channel_ids", set()).discard(chat.id)


if __name__ == '__main__':
    # Enable logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    bot = Bot(mytoken)
    print(bot.create_group_list(link='https://app.simplenote.com/p/MRlJ5H'))
    print(bot.is_group("https://t.me/evilscript"))
