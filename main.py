from config import *
from ll_spn import *
from telegram.ext import Application, ConversationHandler, filters, CommandHandler, MessageHandler, ContextTypes
from telegram import ReplyKeyboardMarkup
import logging
import sqlite3
import aiohttp
import random
import datetime
import requests
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
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
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
        await update.message.reply_text(
            "Представься пожалуйста... ",)
        return 5

    async def greetings(self, update, context):
        reply_keyboard = [['/help']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        first_name = [update.message][0]['chat']['first_name']
        user_name = [update.message][0]['chat']['username']
        if "меня зовут" in update.message.text.lower():
            if len(update.message.text.lower().split(" ")) == 3:
                self.user_id = update.message.text[update.message.text.lower().find("меня зовут") + 11:].capitalize()
            else:
                self.user_id = update.message.text[update.message.text.lower().find("меня зовут") + 11:update.message.text.lower().find(" ")].capitalize()
        else:
            if len(update.message.text.lower().split(" ")) == 1:
                self.user_id = update.message.text.capitalize()
            else:
                self.user_id = update.message.text.capitalize()
        await update.message.reply_text(f"Привет, {self.user_id}! Теперь ты можешь ознакомиться с тем, что я умею)) /help",
                                        reply_markup=markup)
        await context.bot.sendMessage(GROUP_ID,
                                      f"Пользователь {first_name}(@{user_name}) использует Ваш бот)"
                                      f"'\n\n Хотите запретить ему писать сообщения?")
        return ConversationHandler.END

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
        reply_keyboard = [['Комедия'], ['Детектив'], ["Триллер"], ["Фантастика"], ['Другое']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете жанр фильма',
            reply_markup=markup)
        return 3

    async def film_list_delete(self, update, context):
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
        return 6

    async def return_list_delete(self, update, context):
        list_name = update.message.text
        self.user_response = []
        self.user_response.append(list_name)
        new_item = """SELECT film_name FROM films WHERE tg_name = ? AND list_name = ?"""
        result = (self.cur.execute(new_item, (self.user_name, list_name,)).fetchall())
        reply_keyboard = []
        for i in result:
            reply_keyboard.append([f"{i[0]}"])
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете название фильма',
            reply_markup=markup)
        return 5

    async def delete_from_db(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        self.user_response.append(update.message.text)
        new_item = """DELETE FROM films WHERE tg_name = ? and list_name = ? and film_name = ?"""
        self.cur.execute(new_item, (self.user_name, self.user_response[0], self.user_response[1]))
        self.con.commit()
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Успешно удалено',
            reply_markup=markup)
        return ConversationHandler.END

    async def add_to_bd(self, update, context):
        self.user_name = [update.message][0]['chat']['first_name']
        self.user_response.append(update.message.text)
        await update.message.reply_text(
            f"Успех")
        new_item = """INSERT INTO films(tg_name, film_name, genre, list_name) VALUES (?, ?, ?, ?)"""
        self.cur.execute(new_item, (self.user_name, self.user_response[0], self.user_response[1], self.list_name))
        self.con.commit()
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END

    async def stop(self, update, context):
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            'Выберете, что хотите сделать',
            reply_markup=markup)
        return ConversationHandler.END

    async def help(self, update, context):
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(
            f"Я - бот-помощник.\n"
            f"\n<i><b><u>Что я умею:</u></b></i>\n"

            f"\n<b>Простые действия:</b>\n"
            f" --> Я умею здороваться с пользователем\n"
            f" --> Я могу подсказать текущую дату и время\n"
            f" --> Я умею прощаться с пользователем\n"

            f"\n<b>Простые команды:</b>\n"
            f" --> /dialog -- умею поддерживать простой диалог\n"
            f" --> /birthday -- могу посчитать количество дней до вашего дня рождения "
            f"(или любой даты если ввести ее вместо даты др)\n"
            f" --> /weather -- умею рассказывать погоду в конкретном городе\n"

            f"\n<b>Фильмы:</b>\n"
            f" --> /film_list_add -- добавлять новый список Ваших фильмов\n"
            f" --> /film_view_lists -- показать списки фильмов\n"
            f" --> /get_film_name_url -- получить ссылку на фильм по названию\n"
            f" --> /film_delete -- удалять из списка фильм\n"

            f"\n<b>Карта:</b>\n"
            f" --> /map_geocoder -- находит карту любого географического объекта\n"

            f"\n<b>Другое:</b>\n"
            f" --> /help -- помощь с ботом\n"
            f" --> /question -- вопрос к разработчикам\n"
            , parse_mode="html", reply_markup=markup)

    async def map_geocoder(self, update, context):
        reply_keyboard = [['Санкт-Петербург'], ['Якутск'], ["Кострома"]]
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

        try:
            reply_keyboard = [['Привет', 'Время', 'Пока'],
                              ['/dialog', '/birthday', '/weather'],
                              ['/film_list_add', '/film_delete'],
                              ['/get_film_name_url', '/film_view_lists'],
                              ['/map_geocoder'],
                              ['/question']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            toponym = response['response']['GeoObjectCollection']["featureMember"][0]["GeoObject"]
            ll, spn = get_ll_spn(toponym)
            static_api_request = (f"http://static-maps.yandex.ru/1.x/?ll={str(ll[0]) + ',' + str(ll[1])}"
                                  f"&spn={str(spn[0]) + ',' + str(spn[1])}&l=map")
            await context.bot.send_photo(
                update.message.chat_id, static_api_request,
                caption=f"{(response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text'])}",
            reply_markup=markup)
        except:
            reply_keyboard = [['/map_geocoder']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text(f"Чтобы создать запрос вы должны ввести название объекта,"
                                        f" картинку которого вы хотите вывести, например:\n\n"
                                        f"\geocoder Якутск\n\n"
                                        f"Попробуйте ещё раз)", reply_markup=markup)

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
        return 4

    async def return_list(self, update, context):
        list_name = update.message.text
        new_item = """SELECT film_name, genre FROM films WHERE tg_name = ? AND list_name = ?"""
        result = (self.cur.execute(new_item, (self.user_name, list_name,)).fetchall())
        str_content = '|  | ---  НАЗВАНИЕ  --- | -----  ЖАНР  -----\n'
        cnt = 1
        for i in result:
            str_content += (f"{cnt} {i[0][:16]} --- ({i[1][:16]})\n")
            cnt += 1
        await update.message.reply_text(f"{str_content}")
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
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

    async def handle_message(self, update, context):
        user_message = update.message.text.lower().strip()

        if "привет" in user_message:
            await self.send_sticker(update, HELLO_STICKER_ID, HELLO)
        elif "пока" in user_message:
            await self.send_sticker(update, BYE_STICKER_ID, BYE)
            await update.message.reply_text(f"Если я ещё понадоблюсь, \nто напишите /start или /help")
        elif "адрес" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /map_geocoder")
        elif "фильм" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /film_view_lists")
        elif "добавить" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /film_list_add")
        elif "dialog" in user_message or "диалог" in user_message or "Диалог" in user_message or "говор" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /dialog")
        elif "time" in user_message or "врем" in user_message or "час" in user_message or "дата" in user_message:
            time_1 = datetime.datetime.now().strftime('Сейчас %H часов %M минут\n\nEсли тебя интересует, то %d число %M месяца %Y года\n\nЕсли быть точным %H:%M (%S sec)')
            await update.message.reply_text(time_1)
        elif "др" in user_message or "день" in user_message or "рожд" in user_message:
            await update.message.reply_text(f"Мне кажется ты хочешь воспользоваться командой /birthday")
        elif ('help' in user_message or 'помощь' in user_message or 'ты' in user_message or
                  'бот' in user_message or 'умеешь' in user_message or 'делаешь' in user_message or '?' in user_message):
            await self.help(update, context)
        else:
            await update.message.reply_text(random.choice(NOT_STATED))

    async def dialog(self, update, context):
        question = random.choice([1, 2])
        await update.message.reply_text(f"<b>Диалог начат, если хочешь "
                                        f"закончить напиши exit</b>", parse_mode="html")
        if question == 1:
            reply_keyboard = [['Хорошо'],
                              ['Отлично'],
                              ['Плохо'],]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text("Как у тебя дела?", reply_markup=markup)
            return 1
        elif question == 2:
            reply_keyboard = [['Да'],
                              ['Нет'],]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text("Любишь питон?", reply_markup=markup)
            return 2
        else:
            await self.end_dialog(update, context)
            return ConversationHandler.END

    async def end_dialog(self, update, context):
        await update.message.reply_text("Жаль, что вы не хотите поговорить")
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text("Диалог закончен", reply_markup=markup)

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
        reply_keyboard = [['Да'],
                          ['Нет'], ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text('Это из-за погоды?', reply_markup=markup)
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
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text("Хорошо поговорили))", reply_markup=markup)
        return ConversationHandler.END

    async def like_python(self, update, context):
        answ = update.message.text.lower()
        if "exit" in answ or "/" in answ:
            await update.message.reply_text("Жаль, что вы не хотите поговорить")
            await update.message.reply_text("Диалог закончен")
            return ConversationHandler.END
        reply_keyboard = [['Да'],
                          ['Нет'], ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        if "да" in answ or "очень" in answ or "ага" in answ or "норм" in answ:
            await update.message.reply_text("Отлично, я сам написан на питоне)")
            await update.message.reply_text("Хочешь написать тг бота на питоне?", reply_markup=markup)
        elif "нет" in answ or "не" in answ or "хуж" in answ or "плох" in answ or "отврат" in answ:
            await update.message.reply_text("Жалко, мои разработчики очень любят этот язык)")
            await update.message.reply_text("Хочешь написать тг бота на другом языке?", reply_markup=markup)
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
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text("Хорошо поговорили)) Пока))", reply_markup=markup)
        return ConversationHandler.END

    async def question(self, update, context):
        await update.message.reply_text(f"Убедительно просим Вас быть вежливыми, ведь это сообщение отправляется напрямую администраторам")
        reply_keyboard = [['Спасибо Вам большое'],
                          ['Бот классный'], ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(f"Введите текст запроса:", reply_markup=markup)
        return 1

    async def send_question(self, update, context):
        first_name = [update.message][0]['chat']['first_name']
        user_name = [update.message][0]['chat']['username']
        a = update.message.text.lower()
        if ("классн" in a or "хорош" in a or "прекрасн" in a or "замечательн" in a or 'здравствуйте' in a or 'спасибо' in a or 'уважаем' in a or 'извините' in a) and ("не" not in a):
            reply_keyboard = [['Привет', 'Время', 'Пока'],
                              ['/dialog', '/birthday', '/weather'],
                              ['/film_list_add', '/film_delete'],
                              ['/get_film_name_url', '/film_view_lists'],
                              ['/map_geocoder'],
                              ['/question']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text(f"Ваше сообщение отправлено", reply_markup=markup)
        else:
            await update.message.reply_text(f"Ваше сообщение НЕ может быть отправлено((")
            reply_keyboard = [['/question']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text(f"Наши админы очень расстраиваются из-за неконструктивной критики)\n\n"
                                            f"Для вашего же блага советуем использовать слова:\n"
                                            f"'здравствуйте', 'спасибо', 'уважаемый', 'извините'\n"
                                            f"А также словосочетания: 'классный/афигенный бот'", reply_markup=markup)
        await context.bot.sendMessage(GROUP_ID,
                                      f"Получен вопрос от пользователя {first_name}(@{user_name}):\n\n '{update.message.text}"
                                      f"'\n\n Хотите ответить ему в лс?")
        return ConversationHandler.END

    async def birthday(self, update, context):
        reply_keyboard = [['1 января'],
                          ['12 мая'], ]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(f"Введите дату своего рождения (в формате: 'число месяц')", reply_markup=markup)
        return 1

    async def count_birthday(self, update, context):
        a = update.message.text.lower().split(" ")
        if len(a) != 2:
            await update.message.reply_text(f"Мы не можем распознать дату(\nПопробуйте ещё раз\nНапример: 1 января")
            return ConversationHandler.END
        try:
            d = int(a[0])
            if a[1][0] in "0123456789":
                m = int(a[1])
            else:
                if "янв" in a[1]:
                    m = 1
                elif "фев" in a[1]:
                    m = 2
                elif "мар" in a[1]:
                    m = 3
                elif "апр" in a[1]:
                    m = 4
                elif "ма" in a[1]:
                    m = 5
                elif "июн" in a[1]:
                    m = 6
                elif "июл" in a[1]:
                    m = 7
                elif "авг" in a[1]:
                    m = 8
                elif "сен" in a[1]:
                    m = 9
                elif "окт" in a[1]:
                    m = 10
                elif "ноя" in a[1]:
                    m = 11
                elif "дек" in a[1]:
                    m = 12
                else:
                    await update.message.reply_text(
                        f"Мы не можем распознать дату(\nПопробуйте ещё раз\nНапример: 1 января")
                    return ConversationHandler.END
        except:
            reply_keyboard = [['/birthday']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text(f"Мы не можем распознать дату(\nПопробуйте ещё раз\nНапример: 1 января", reply_markup=markup)
            return ConversationHandler.END
        now = datetime.datetime.now()
        other_date = datetime.datetime(day=d, month=m, year=2025)
        if other_date < now:
            other_date = datetime.datetime(day=d, month=m, year=2026)
        delta = other_date - now
        days = delta.days
        seconds = delta.seconds
        reply_keyboard = [['Привет', 'Время', 'Пока'],
                          ['/dialog', '/birthday', '/weather'],
                          ['/film_list_add', '/film_delete'],
                          ['/get_film_name_url', '/film_view_lists'],
                          ['/map_geocoder'],
                          ['/question']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        if days == 0:
            await update.message.reply_text(f"До вашего др осталось:\n{seconds // 3600} часов, "
                                            f"{(seconds % 3600) // 60} минут, {seconds % 60} секунд))\nУже совсем скоро)", reply_markup=markup)
        else:
            await update.message.reply_text(f"До вашего др осталось:\n{days} дней, {seconds // 3600} часов, "
                                        f"{(seconds % 3600) // 60} минут, {seconds % 60} секунд))\nУже совсем скоро)", reply_markup=markup)
        return ConversationHandler.END

    async def weather(self, update, context):
        reply_keyboard = [['Санкт-Петербург'],
                          ['Москва'],
                          ['Тула'],
                          ['Псков'],]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        await update.message.reply_text(f"Введите название города, в котором хотите узнать погоду)", reply_markup=markup)
        return 1

    async def get_weather(self, update, context):
        try:
            town = update.message.text
            u = f"http://api.openweathermap.org/data/2.5/weather"
            params = {"q": town,
                      "lang": "ru",
                      "units": "metric",
                      "appid": API_WEATHER_KEY,}
            response = requests.get(u, params)
            data = response.json()
            description = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            temp_min = data["main"]["temp_min"]
            temp_max = data["main"]["temp_max"]
            pressure = data["main"]["pressure"]
            humidity = data["main"]["humidity"]
            speed = data["wind"]["speed"]
            reply_keyboard = [['Привет', 'Время', 'Пока'],
                              ['/dialog', '/birthday', '/weather'],
                              ['/film_list_add', '/film_delete'],
                              ['/get_film_name_url', '/film_view_lists'],
                              ['/map_geocoder'],
                              ['/question']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text(f"ПОГОДА ДЛЯ ГОРОДА {town.upper()}:\n\n"
                                            f"Прогноз: {description}\n"
                                            f"Температура: +{int(temp)}℃\n (+{temp_min}℃ - +{temp_max}℃)\n"
                                            f"Ощущается как: +{int(feels_like)}℃\n"
                                            f"Давление: {pressure // 1.333} мм рт ст\n"
                                            f"Влажность: {humidity}%\n"
                                            f"Скорость ветра: {speed} м/с\n", reply_markup=markup)
        except:
            reply_keyboard = [['/weather']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
            await update.message.reply_text("Проверьте название города!", reply_markup=markup)
        return ConversationHandler.END

    def main(self):
        film_dialog = ConversationHandler(
            entry_points=[CommandHandler('film_list_add', self.film_list_add),
                          CommandHandler('film_view_lists', self.film_view_lists),
                          CommandHandler('film_delete', self.film_list_delete),
                          ],
            states={
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.make_list)],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_data)],
                3: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_to_bd)],
                4: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.return_list)],
                5: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.delete_from_db)],
                6: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.return_list_delete)],

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

        question_to_testing = ConversationHandler(
            entry_points=[CommandHandler("question", self.question),],
            states={
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_question)],
            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )

        birthday = ConversationHandler(
            entry_points=[CommandHandler("birthday", self.birthday),],
            states={
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.count_birthday)],
            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )

        weather = ConversationHandler(
            entry_points=[CommandHandler("weather", self.weather),],
            states={
                1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_weather)],
            },
            fallbacks=[CommandHandler('stop', self.stop)]
        )

        application = Application.builder().token(TOKEN).build()
        application.add_handler(film_dialog)
        application.add_handler(greeting)
        application.add_handler(geocoder)
        application.add_handler(dialog)
        application.add_handler(film_url_dialog)
        application.add_handler(question_to_testing)
        application.add_handler(birthday)
        application.add_handler(weather)
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Инструменты разработчика:
        application.add_handler(CommandHandler("geocoder_test", self.geocoder_test))

        application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    tg = TG_BOT()
    tg.main()
