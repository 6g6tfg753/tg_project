from config import *
from telegram.ext import Application, ConversationHandler, filters, CommandHandler, MessageHandler
from telegram import ReplyKeyboardMarkup
import logging
import sqlite3


class TG_BOT():
    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
        )

        logger = logging.getLogger(__name__)
        self.con = sqlite3.connect('film_db.sqlite')
        self.cur = self.con.cursor()
        self.user_response = []

    async def start(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        reply_keyboard = [['/make_list', '/button2']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "здесь будет описание и список команд",
            reply_markup=markup)

    async def make_list(self, update, context):
        reply_keyboard = [['/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Введите название фильма',
            reply_markup=markup)
        return 1

    async def get_data(self, update, context):
        self.user_response.append(update.message.text)
        reply_keyboard = [['Комедия', 'Детектив', 'Другое']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете жанр',
            reply_markup=markup)
        return 2

    async def add_to_bd(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        self.user_response.append(update.message.text)
        await update.message.reply_text(
            f"Успех")
        new_item = """INSERT INTO films(tg_name, film_name, genre) VALUES (?, ?, ?)"""
        self.cur.execute(new_item, (self.user_name, self.user_response[0], self.user_response[1]))
        self.con.commit()
        return ConversationHandler.END

    async def stop(self, update, context):
        reply_keyboard = [['/make_list', '/button2']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END



    def main(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('make_list', self.make_list)],
            states={
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_data)],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_to_bd)]

            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )
        application = Application.builder().token(TOKEN).build()
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("start", self.start))
        application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    tg = TG_BOT()
    tg.main()