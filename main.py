from config import *
from requirements import *
from telegram.ext import Application, ConversationHandler, filters, CommandHandler, MessageHandler, ContextTypes
from telegram import ReplyKeyboardMarkup
import logging
import sqlite3
import aiohttp
import random


class TG_BOT():
    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
        )

        self.logger = logging.getLogger(__name__)
        self.con = sqlite3.connect('film_db.sqlite')
        self.cur = self.con.cursor()
        self.user_response = []
        self.dialog_flag = False

    async def start(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        reply_keyboard = [['/film_list_add', '/film_view_lists', '/map_geocoder']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "Мы рады тебя приветствовать) Если хочешь узнать что умеет бот напиши /help",
            reply_markup=markup)

    async def film_list_add(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        new_item = """SELECT list_name FROM films WHERE tg_name = ?"""
        lists = set(self.cur.execute(new_item, (self.user_name,)).fetchall())
        reply_keyboard = []
        for i in lists:
            reply_keyboard.append([f"{str(i)[2:-3]}"])
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете список. Чтобы создать новый список введите его название',
            reply_markup=markup)
        return 1

    async def make_list(self, update, context):
        self.list_name = update.message.text
        reply_keyboard = [['/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Введите название фильма',
            reply_markup=markup)
        return 2

    async def get_data(self, update, context):
        self.user_response = []
        self.user_response.append(update.message.text)
        reply_keyboard = [['Комедия', 'Детектив', "Триллер", "Фантастика", 'Другое']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете жанр фильма',
            reply_markup=markup)
        return 3

    async def add_to_bd(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        self.user_response.append(update.message.text)
        await update.message.reply_text(
            f"Успех")
        new_item = """INSERT INTO films(tg_name, film_name, genre, list_name) VALUES (?, ?, ?, ?)"""
        self.cur.execute(new_item, (self.user_name, self.user_response[0], self.user_response[1], self.list_name))
        self.con.commit()
        reply_keyboard = [['/film_list_add', '/film_view_lists', '/map_geocoder']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END

    async def stop(self, update, context):
        reply_keyboard = [['/film_list_add', '/film_view_lists', "/map_geocoder"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END

    async def help(self, update, context):
        await update.message.reply_text(
            f"Я - бот-помощник.\n"
            f"\n<i><b><u>Что я умею:</u></b></i>\n"

            f"\n<b>Диалог:</b>\n"
            f" --> Я умею здороваться с пользователем\n"
            f" --> Я пока что умею поддерживать простой диалог по кодовому слову 'диалог'\n"
            f" --> Я умею прощаться с пользователем\n"
            
            f"\n<b>Фильмы:</b>\n"
            f" --> /film_list_add -- добавлять новый список Ваших фильмов\n"
            f" --> /film_view_lists -- показать списки фильмов\n"
            # TODO: f" --> /film_delete -- удалять из списка фильм\n"
            # TODO: f" --> /film_watch -- выбрать фильм для просмотра из списка всех фильмов\n"

            f"\n<b>Карта:</b>\n"
            f" --> /map_geocoder -- находит карту любого географического объекта\n"  # TODO: выделить объект на карте
            f"\n<b>Напоминания:</b>\n"
            # TODO: f" --> /reminding ~_время напоминания_~ (в формате HH::MM (DD:MM:YY)) ~_количество сообщений_~ (3 по умолчанию) --  установить напоминание\n" 
            # TODO: f" --> /timer ~_на какое время таймер_~ (в формате HH::MM) ~_количество сообщений_~ (1 по умолчанию) --  установить таймер, который сработает через определенное количество времени\n" 

            f"\n<b>Другое:</b>\n"
            f" --> /help -- помощь с ботом\n"
            # TODO: f" --> /question -- вопрос к разработчикам\n"
            , parse_mode="html")

    async def map_geocoder(self, update, context):
        reply_keyboard = [['Санкт-Петербург', 'Якутск', "Кострома"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Напишите название объекта',
            reply_markup=markup)
        return 4


    async def send_map_object(self, update, context):
        self.user_response = []
        self.user_response.append(update.message.text)
        geocoder_uri = "http://geocode-maps.yandex.ru/1.x/"
        response = await self.get_response(geocoder_uri, params={
            "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
            "format": "json",
            "geocode": self.user_response[0]
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
                                         f" картинку которого вы хотите вывести, например:\n\n"
                                         f"\geocoder Якутск\n\n"
                                         f"Попробуйте ещё раз)")

            return
        toponym = response['response']['GeoObjectCollection']["featureMember"][0]["GeoObject"]
        print(toponym)
        print(self.user_response)
        ll, spn = get_ll_spn(toponym)
        static_api_request = (f"http://static-maps.yandex.ru/1.x/?ll={str(ll[0]) + ',' + str(ll[1])}"
                              f"&spn={str(spn[0]) + ',' + str(spn[1])}&l=map")
        await context.bot.send_photo(
            update.message.chat_id, static_api_request,
            caption=f"{(response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text'])}"
        )
        return ConversationHandler.END


    async def geocoder_test(self, update, context):
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
                                         f" картинку которого вы хотите вывести, например:\n\n"
                                         f"\geocoder Якутск\n\n"
                                         f"Попробуйте ещё раз)")

            return ConversationHandler.END
        toponym = response['response']['GeoObjectCollection']["featureMember"][0]["GeoObject"]
        ll, spn = get_ll_spn(toponym)
        static_api_request = (f"http://static-maps.yandex.ru/1.x/?ll={str(ll[0]) + ',' + str(ll[1])}"
                              f"&spn={str(spn[0]) + ',' + str(spn[1])}&l=map")
        await context.bot.send_photo(
            update.message.chat_id, static_api_request,
            caption=f"{(response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text'])}"
        )
        return ConversationHandler.END

    async def get_response(self, url, params):
        self.logger.info(f"getting {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                return await resp.json()

    async def film_view_lists(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        new_item = """SELECT list_name FROM films WHERE tg_name = ?"""
        lists = set(self.cur.execute(new_item, (self.user_name,)).fetchall())
        reply_keyboard = []
        for i in lists:
            reply_keyboard.append([f"{str(i)[2:-3]}"])
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете список',
            reply_markup=markup)
        return 11

    async def return_list(self, update, context):
        list_name = update.message.text
        new_item = """SELECT film_name, genre FROM films WHERE tg_name = ? AND list_name = ?"""
        result = (self.cur.execute(new_item, (self.user_name, list_name,)).fetchall())
        list_content = []
        for i in result:
            list_content.append(f"название: {i[0]}, жанр: {i[1]}")
        await update.message.reply_text(f"{list_content}")
        reply_keyboard = [['/film_list_add', '/film_view_lists', '/map_geocoder']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END

    async def handle_message(self, update, context):
        user_message = update.message.text.lower().strip()

        if self.dialog_flag == False:
            if "привет" in user_message:
                try:
                    await update.message.reply_sticker(random.choice(HELLO_STICKER_ID))
                except Exception as e:
                    logging.error(f"Ошибка при отправке стикера: {e}")
                    await update.message.reply_text("Не могу отправить стикер :(")
            elif "пока" in user_message:
                try:
                    await update.message.reply_sticker(random.choice(BYE_STICKER_ID))
                except Exception as e:
                    logging.error(f"Ошибка при отправке стикера: {e}")
                    await update.message.reply_text("Не могу отправить стикер :(")
            if 'help' in user_message or 'помощь' in user_message or 'ты' in user_message or 'бот' in user_message or'умеешь' in user_message or'делаешь' in user_message:
                await self.help(update, context)
            elif "адрес" in user_message:
                await self.map_geocoder(update, context)
            elif "фильм" in user_message:
                await self.film_view_lists(update, context)
            elif "добавить" in user_message:
                await self.film_list_add(update, context)
            elif "говор" in user_message or "диалог" in user_message:
                self.dialog_flag = True
                await update.message.reply_text("Диалог начат, если хочешь закончить напиши выход или exit")
                await update.message.reply_text("Привет) Как дела?")
                try:
                    await update.message.reply_sticker(random.choice(HELLO_STICKER_ID))
                except Exception as e:
                    logging.error(f"Ошибка при отправке стикера: {e}")
                    await update.message.reply_text("Не могу отправить стикер :(")
            else:
                await update.message.reply_text(random.choice(NOT_STATED))
        else:
            if "exit" in user_message or 'exit' in user_message:
                self.dialog_flag = False
                await update.message.reply_text("Рад был поболтать)")
                try:
                    await update.message.reply_sticker(random.choice(BYE_STICKER_ID))
                except Exception as e:
                    logging.error(f"Ошибка при отправке стикера: {e}")
                    await update.message.reply_text("Не могу отправить стикер :(")
            elif any(el in user_message for el in ["хорош", "отличн", "неплох", "норм"]):
                await update.message.reply_text("С позитивными людьми приятно иметь дело)")
            elif any(el in user_message for el in ["ужасн", "хуж", "плох", "ну", "отврат"]):
                await update.message.reply_text("Да ладно, всё равно неплохо поболтали, да ведь?")
            else:
                await update.message.reply_text("Дамц, в жизни все сложнее чем просто хорошо или плохо)(")
            self.dialog_flag = False
            await update.message.reply_text("Рад был поболтать)")
            try:
                await update.message.reply_sticker(random.choice(BYE_STICKER_ID))
            except Exception as e:
                logging.error(f"Ошибка при отправке стикера: {e}")

    def main(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('film_list_add', self.film_list_add),
                          CommandHandler('film_view_lists', self.film_view_lists),
                          CommandHandler('map_geocoder', self.map_geocoder),
                          ],
            states={
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.make_list)],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_data)],
                3: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_to_bd)],
                11: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.return_list)],
                4: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_map_object)],
            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )
        application = Application.builder().token(TOKEN).build()
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Инструменты разработчика:
        application.add_handler(CommandHandler("geocoder_test", self.geocoder_test))

        application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    tg = TG_BOT()
    tg.main()
