from config import *
from ll_spn import *
from telegram.ext import Application, ConversationHandler, filters, CommandHandler, MessageHandler, ContextTypes
from telegram import ReplyKeyboardMarkup
import logging
import sqlite3
import aiohttp
import random
from parser import parse


class TG_BOT():
    def __init__(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
        )

        self.logger = logging.getLogger(__name__)
        self.con = sqlite3.connect('film_db.sqlite')
        self.cur = self.con.cursor()
        self.user_response = []

    async def get_film_name_url(self, update, context):
        reply_keyboard = [['/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Введите название фильма, ссылку на который вы хотите получить',
            reply_markup=markup)
        return 2

    async def get_url(self, update, context):
        reply_keyboard = [['/film_list_add', '/film_view_lists', '/map_geocoder', '/get_film_name_url']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        a = parse(update.message.text)
        if len(a) == 0:
            await update.message.reply_text("мы не смогли найти этот фильм, попробуйте ещё раз((")
            return ConversationHandler.END
        await update.message.reply_text("Скорее всего вы искали:\n" + a[0],
            reply_markup=markup)
        if len(a) == 1:
            return ConversationHandler.END
        b = "Вот  что ещё мы нашли:\n"
        c = list(map(str, [a[i] for i in range(len(a)) if i != 0]))
        for el in c:
            b += str(c.index(el) + 1) + ".) " + el + "\n"
        await update.message.reply_text(b,
            reply_markup=markup)
        return ConversationHandler.END

    async def start(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        reply_keyboard = [['/film_list_add', '/film_view_lists', '/map_geocoder', '/get_film_name_url']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            "Представься пожалуйста... ",
            reply_markup=markup)
        return 5


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
        reply_keyboard = [['/film_list_add', '/film_view_lists', '/map_geocoder', '/get_film_name_url']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END

    async def stop(self, update, context):
        reply_keyboard = [['/film_list_add', '/film_view_lists', '/map_geocoder', '/get_film_name_url']]
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
            f" --> Я пока что умею поддерживать простой диалог по команде /dialog\n"
            f" --> Я умею прощаться с пользователем\n"

            f"\n<b>Фильмы:</b>\n"
            f" --> /film_list_add -- добавлять новый список Ваших фильмов\n"
            f" --> /film_view_lists -- показать списки фильмов\n"
            f" --> /get_film_name_url -- получить ссылку на фильм по названию\n"
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
        reply_keyboard = [['Санкт-Петербург', 'Якутск', "Кострома", '/stop']]
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
        if str(update.message.text)== "":
            print("error! no geo-object!")
            await context.bot.sendMessage(
                update.message.chat_id, f"Чтобы создать запрос вы должны ввести название объекта,"
                                        f" картинку которого вы хотите вывести, например:\n\n"
                                        f"Якутск\n\n"
                                        f"Попробуйте ещё раз)")
            return
        elif (response['response']['GeoObjectCollection']["featureMember"] == []):
            print("error! geo-object not found!")
            await context.bot.sendMessage(
                update.message.chat_id, f"Чтобы создать запрос вы должны ввести название объекта,"
                                        f" картинку которого вы хотите вывести, например:\n\n"
                                        f"Якутск\n\n"
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
                update.message.chat_id, f"Чтобы создать запрос вы должны ввести название объекта,"
                                        f" картинку которого вы хотите вывести, например:\n\n"
                                        f"\geocoder Якутск\n\n"
                                        f"Попробуйте ещё раз)")
            return
        elif (response['response']['GeoObjectCollection']["featureMember"] == []):
            print("error! geo-object not found!")
            await context.bot.sendMessage(
                update.message.chat_id, f"Чтобы создать запрос вы должны ввести название объекта,"
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
        str_content = ''
        for i in result:
            str_content += (f"Название: {i[0]}, жанр: {i[1]}\n")
        await update.message.reply_text(f"{str_content}")
        reply_keyboard = [['/film_list_add', '/film_view_lists', '/map_geocoder', '/get_film_name_url']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END

    async def send_sticker(self, update, mas, MESS=['']):
        await update.message.reply_text(random.choice(MESS))
        try:
            await update.message.reply_sticker(random.choice(mas))
        except Exception as e:
            logging.error(f"Ошибка при отправке стикера: {e}")

    async def greetings(self, update, context):
        self.user_id = update.message.text
        await update.message.reply_text(f"Привет, {self.user_id}! Теперь ты можешь ознакомиться с тем, что я умею)) /help")
        return ConversationHandler.END

    async def handle_message(self, update, context):
        user_message = update.message.text.lower().strip()

        if "привет" in user_message:
            await self.send_sticker(update, HELLO_STICKER_ID, HELLO)
        elif "пока" in user_message:
            await self.send_sticker(update, BYE_STICKER_ID, BYE)
            await update.message.reply_text(f"Если я ещё понадоблюсь, \nто напишите /start или /help")
        elif ('help' in user_message or 'помощь' in user_message or 'ты' in user_message or
                'бот' in user_message or 'умеешь' in user_message or 'делаешь' in user_message or '?' in user_message):
            await self.help(update, context)
        elif "адрес" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /map_geocoder")
        elif "фильм" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /film_view_lists")
        elif "добавить" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /film_list_add")
        elif "dialog" in user_message or "диалог" in user_message or "Диалог" in user_message or "говор" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /dialog")
        else:
            await update.message.reply_text(random.choice(NOT_STATED))

    async def dialog(self, update, context):
        question = random.choice([1, 2])
        await update.message.reply_text(f"<b>Диалог начат, если хочешь "
                                        f"закончить напиши exit</b>", parse_mode="html")
        if question == 1:
            await update.message.reply_text("Как у тебя дела?")
            return 1
        elif question == 2:
            await update.message.reply_text("Любишь питон?")
            return 2
        else:
            await self.end_dialog(update, context)
            return ConversationHandler.END

    async def end_dialog(self, update, context):
        await update.message.reply_text("Жаль, что вы не хотите поговорить")
        await update.message.reply_text("Диалог закончен")

    async def is_weather(self, update, context):
        answ = update.message.text.lower()
        if "exit" in answ or "/" in answ:
            await update.message.reply_text("Жаль, что вы не хотите поговорить")
            await update.message.reply_text("Диалог закончен")
            return ConversationHandler.END
        if "хорош" in answ or "отличн" in answ or "неплох" in answ or "норм" in answ:
            await update.message.reply_text("С позитивными людьми приятно иметь дело)")
        elif "ну" in answ or "ужасн" in answ or "хуж" in answ or "плох" in answ or "отврат" in answ:
            await update.message.reply_text("Да ладно, всё равно неплохо поболтали, да ведь?")
        else:
            await update.message.reply_text("Дамц, в жизни все сложнее чем просто хорошо или плохо)(")
        await update.message.reply_text('Это из-за погоды?')
        return 11

    async def yes_or_no(self, update, context):
        answ = update.message.text.lower()
        if "exit" in answ or "/" in answ:
            await update.message.reply_text("Жаль, что вы не хотите поговорить")
            await update.message.reply_text("Диалог закончен")
            return ConversationHandler.END
        if "да" in answ or "отличн" in answ or "неплох" in answ or "норм" in answ:
            await update.message.reply_text("Погода поменяется и настроение тоже...)")
        elif "нет" in answ or "ужасн" in answ or "хуж" in answ or "плох" in answ or "отврат" in answ:
            await update.message.reply_text("Да ладно, всё равно неплохо поболтали, да ведь?")
        else:
            await update.message.reply_text("Хм... в жизни все сложнее чем просто да или нет)(")
        await update.message.reply_text("Хорошо поговорили))")
        return ConversationHandler.END

    async def like_python(self, update, context):
        answ = update.message.text.lower()
        if "exit" in answ or "/" in answ:
            await update.message.reply_text("Жаль, что вы не хотите поговорить")
            await update.message.reply_text("Диалог закончен")
            return ConversationHandler.END
        if "да" in answ or "очень" in answ or "ага" in answ or "норм" in answ:
            await update.message.reply_text("Отлично, я сам написан на питоне?")
            await update.message.reply_text("Хочешь написать тг бота на питоне?")
        elif "нет" in answ or "не" in answ or "хуж" in answ or "плох" in answ or "отврат" in answ:
            await update.message.reply_text("Жалко, мои разработчики очень любят этот язык)")
            await update.message.reply_text("Хочешь написать тг бота на другом языке?")
        else:
            await update.message.reply_text("Так да или нет?")
            return 2
        return 21

    async def write_tg(self, update, context):
        answ = update.message.text.lower()
        if "exit" in answ or "/" in answ:
            await update.message.reply_text("Жаль, что вы не хотите поговорить")
            await update.message.reply_text("Диалог закончен")
            return ConversationHandler.END
        if "да" in answ or "конечно" in answ or "ага" in answ or "хо" in answ:
            await update.message.reply_text("Класс, попробуй, у тебя получится)))")
        elif "нет" in answ or "ни" in answ:
            await update.message.reply_text("Жаль((( на самом деле это интересно(")
        else:
            await update.message.reply_text("Это да или нет?")
            return 21
        await update.message.reply_text("Хорошо поговорили)) Пока))")
        return ConversationHandler.END


    def main(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('film_list_add', self.film_list_add),
                          CommandHandler('film_view_lists', self.film_view_lists),
                          ],
            states={
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.make_list)],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_data)],
                3: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_to_bd)],
                11: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.return_list)],
            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )

        greeting = ConversationHandler(
            entry_points=[CommandHandler("start", self.start),],
            states={
                5: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.greetings)]
            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )

        geocoder = ConversationHandler(
            entry_points=[CommandHandler("map_geocoder", self.map_geocoder),],
            states={
                4: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_map_object)],
            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )

        dialog = ConversationHandler(
            entry_points=[CommandHandler("dialog", self.dialog),],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.end_dialog)],
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.is_weather)],
                11: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.yes_or_no)],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.like_python)],
                21: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.write_tg)],
                1000: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.dialog)],

            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )

        film_url_dialog = ConversationHandler(
            entry_points=[CommandHandler("get_film_name_url", self.get_film_name_url),],
            states={
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_url)],
            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )

        application = Application.builder().token(TOKEN).build()
        application.add_handler(conv_handler)
        application.add_handler(greeting)
        application.add_handler(geocoder)
        application.add_handler(dialog)
        application.add_handler(film_url_dialog)
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Инструменты разработчика:
        application.add_handler(CommandHandler("geocoder_test", self.geocoder_test))

        application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    tg = TG_BOT()
    tg.main()
