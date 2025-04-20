from config import *
from telegram.ext import Application, ConversationHandler, filters, CommandHandler, MessageHandler
from telegram import ReplyKeyboardMarkup
import logging
import sqlite3
import requests
import aiohttp


class TG_BOT():
    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
        )

        self.logger = logging.getLogger(__name__)
        self.con = sqlite3.connect('film_db.sqlite')
        self.cur = self.con.cursor()
        self.user_response = []

    async def start(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        reply_keyboard = [['/make_list', '/button2', '/geocoder']]
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
        reply_keyboard = [['/make_list', '/button2', "/geocoder"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END

    async def help(self, update, context):
        await update.message.reply_text(
            f"Я бот.\n"
            f"Что умеет этот бот:\n"
            f"/make_list -- добавить в список фильм\n"
            f"/geocoder (Город) -- найти картинку города\n"
            f"/help -- помощь с ботом\n")

    def get_ll_spn(self, toponym):
        ll = list(map(lambda x: str(x), toponym["Point"]["pos"].split()))
        lowercorner = list(map(lambda x: float(x), toponym["boundedBy"]["Envelope"]["lowerCorner"].split()))
        uppercorner = list(map(lambda x: float(x), toponym["boundedBy"]["Envelope"]["upperCorner"].split()))
        spn = list(map(lambda x: str(x), [uppercorner[0] - lowercorner[0], uppercorner[1] - lowercorner[1]]))
        return ll, spn

    async def geocoder(self, update, context):
        geocoder_uri = "http://geocode-maps.yandex.ru/1.x/"
        response = await self.get_response(geocoder_uri, params={
            "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
            "format": "json",
            "geocode": update.message.text
        })
        if str(update.message.text)[10:] == "":
            print("error! no geo-object!")
            await context.bot.sendMessage(
                update.message.chat_id,  f"Чтобы создать запрос вы должны ввести название объекта,"
                                         f" картинку которого вы хотите вывести, например:\n\n"
                                         f"\geocoder Якутск\n\n"
                                         f"Попробуйте ещё раз)")
            return
        elif (response['response']['GeoObjectCollection']["featureMember"] == []):
            print("error! geo-object not found!")
            await context.bot.sendMessage(
                update.message.chat_id,  f"Чтобы создать запрос вы должны ввести название объекта,"
                                         f" картинку которого вы хотите вывести, например:\n"
                                         f"\geocoder Якутск\n\n"
                                         f"Попробуйте ещё раз)")

            return
        toponym = response['response']['GeoObjectCollection']["featureMember"][0]["GeoObject"]
        ll, spn = self.get_ll_spn(toponym)
        static_api_request = (f"http://static-maps.yandex.ru/1.x/?ll={str(ll[0]) + ',' + str(ll[1])}"
                              f"&spn={str(spn[0]) + ',' + str(spn[1])}&l=map")
        await context.bot.send_photo(
            update.message.chat_id, static_api_request,
            caption=f"{(response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text'])}"
        )

    async def get_response(self, url, params):
        self.logger.info(f"getting {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                return await resp.json()

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
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("geocoder", self.geocoder))
        application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    tg = TG_BOT()
    tg.main()
