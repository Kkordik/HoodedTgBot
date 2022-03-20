from lang_texts import texts
from passw import *
import logging
import aiomysql
import pymysql
from pymysql import cursors
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
import time


bot = Bot(token=API_TOKEN)


storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Function sending a start message (private chat)
async def start_msg(msg_chat, user_db):
    start_markup = types.InlineKeyboardMarkup(1)
    st_mp_send_msg = types.InlineKeyboardButton(text=texts[user_db.language]["st_mark_wr"],
                                                callback_data="send message group")
    st_mp_add_gp = types.InlineKeyboardButton(text=texts[user_db.language]["st_mark_addgr"],
                                              url='http://t.me/HoodedBot?startgroup=test')
    st_mp_write_ls = types.InlineKeyboardButton(text=texts[user_db.language]["st_mark_wrls"],
                                                callback_data="send message ls")
    st_mp_buy_bfly = types.InlineKeyboardButton(text=texts[user_db.language]["st_mark_buy"],
                                                callback_data="buy bfly")
    start_markup.add(st_mp_send_msg)
    start_markup.add(st_mp_write_ls)
    start_markup.add(st_mp_add_gp)
    start_markup.add(st_mp_buy_bfly)

    await bot.send_message(msg_chat.id, texts[user_db.language]["st_msg_priv"].format(user_db.bfly),
                           reply_markup=start_markup, parse_mode="HTML")


class Form(StatesGroup):
    to_chat_id = State()
    from_chat_id = State()
    del_message = State()
    message = State()


class Cost(StatesGroup):
    new_cost = State()
    chat_id = State()


class ChatDb:
    def __init__(self, chatid):
        self.chatid = chatid
        self.cost = None
        self.sended = None
        self.title = None
        self.username = None

    # It is async method collecting/adding info about CHAT in Database
    async def search_chat(self):
        try:
            try:
                chat = await bot.get_chat(self.chatid)
                self.title = chat.title
                self.username = chat.username
            except Exception:
                pass

            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )

            try:

                with connection.cursor() as cursor:
                    select_all_users = "SELECT * FROM chats WHERE chat_id = {}".format(self.chatid)
                    cursor.execute(select_all_users)
                    chat_db = cursor.fetchone()
                    if chat_db is not None:
                        self.cost = chat_db['cost']
                        self.sended = chat_db['sended']
                    else:
                        self.cost = start_chat_cost
                        self.sended = 0
                        insert_user = "INSERT IGNORE INTO chats(chat_id, cost, sended) VALUES ({}, {}, {})" \
                            .format(self.chatid, self.cost, self.sended)
                        cursor.execute(insert_user)

            finally:
                connection.commit()
                connection.close()

        except Exception as ex:
            print("Connection refused... def search_chat")
            print(ex)

    async def edit_cost(self, new_cost):
        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            try:
                with connection.cursor() as cursor:
                    update_cost = "UPDATE chats SET cost = {} WHERE chat_id = {}".format(new_cost, self.chatid)
                    cursor.execute(update_cost)
            finally:
                connection.commit()
                connection.close()
        except Exception as ex:
            print("Connection refused... def edit_cost")
            print(ex)

    async def send(self, from_chat_id, message_id):
        try:
            await bot.copy_message(self.chatid, from_chat_id, message_id)
            try:
                connection = pymysql.connect(
                    host=host,
                    port=3306,
                    user=user,
                    password=password,
                    database=db_name,
                    cursorclass=pymysql.cursors.DictCursor
                )
                try:
                    with connection.cursor() as cursor:
                        update_cost = "UPDATE chats SET sended = sended + 1 WHERE chat_id = {}".format(self.chatid)
                        cursor.execute(update_cost)
                finally:
                    connection.commit()
                    connection.close()
            except Exception as ex:
                print("Connection refused... def send")
                print(ex)
        except Exception as exx:
            print("Connection refused... def send/ may be blocked")
            print(exx)


class UserDb:
    def __init__(self, userid):
        self.userid = userid
        self.language = None
        self.bfly = None
        self.first_name = None
        self.username = None
        self.chats = []

        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            try:
                with connection.cursor() as cursor:
                    select_language = "SELECT language FROM users WHERE user_id = {}".format(self.userid)
                    cursor.execute(select_language)
                    language = cursor.fetchone()
                    self.language = language["language"]
            finally:
                connection.commit()
                connection.close()
        except Exception as ex:
            print("Connection refused... def UserDb")
            print(ex)

    # It is async method collecting/adding info about USER in Database
    async def search_user(self):
        try:
            try:
                chat = await bot.get_chat(self.userid)
                self.first_name = chat.first_name
                self.username = chat.username
            except Exception:
                pass
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )

            try:

                with connection.cursor() as cursor:
                    select_all_users = "SELECT * FROM users WHERE user_id = {}".format(self.userid)
                    cursor.execute(select_all_users)
                    user_db = cursor.fetchone()
                    if user_db is not None:
                        self.bfly = user_db['money']
                    else:
                        self.bfly = starty_numb_bfly
                        insert_user = "INSERT IGNORE INTO users(user_id, money) VALUES ({}, {})"\
                            .format(self.userid, self.bfly, self.messages)
                        cursor.execute(insert_user)

            finally:
                connection.commit()
                connection.close()

        except Exception as ex:
            print("Connection refused... def search_user")
            print(ex)

    # It is async method collecting all USER'S CHATS from Database into []
    async def find_chats(self, statuses):
        try:
            connection = await aiomysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                db=db_name,
            )

            try:

                async with await connection.cursor() as cursor:
                    select_all_chats = "SELECT chat_id FROM chats"
                    await cursor.execute(select_all_chats)
                    all_chats = await cursor.fetchall()
                    for chat in all_chats:
                        try:
                            member = await bot.get_chat_member(chat[0], self.userid)
                            status = member.status
                            if status in statuses:
                                yield chat[0]
                        except Exception:
                            pass
                    await cursor.close()
            finally:
                await connection.commit()
                connection.close()
        except Exception as ex:
            print("Connection refused... def find_chats")
            print(ex)

    # Method which edits number of bfly(money) for current user | format :  edition = '+1' / edition = '-2'
    async def edit_bfly(self, edition):
        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            try:
                with connection.cursor() as cursor:
                    edit_bfly_cmd = "UPDATE users SET money = money {} WHERE user_id = {}".format(edition, self.userid)
                    cursor.execute(edit_bfly_cmd)
            finally:
                connection.commit()
                connection.close()
        except Exception as ex:
            print("Connection refused... def edit_bfly")
            print(ex)

    # Method which edits language for current user | format :  lang = 'ua' / 'ru' / 'en'
    async def edit_lang(self, lang):
        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=password,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            try:
                with connection.cursor() as cursor:
                    edit_lang_cmd = "UPDATE users SET language = '{}'WHERE user_id = {}".format(lang, self.userid)
                    cursor.execute(edit_lang_cmd)
            finally:
                connection.commit()
                connection.close()
        except Exception as ex:
            print("Connection refused... def edit_lang")
            print(ex)


# Start command handling
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):

    msg_chat = message.chat

    user_db = UserDb(message.from_user.id)

    # Two types of start private and not
    if message.chat.type == 'private':

        await user_db.search_user()
        if message.text == "/start":
            await start_msg(msg_chat, user_db)
        else:
            chat_send_db = ChatDb(message.text.split(" ")[1])  # Sending a message by a button in group
            await chat_send_db.search_chat()

            if chat_send_db.cost <= user_db.bfly:
                msg = await bot.send_message(user_db.userid, texts[user_db.language]["before_sending"].format(
                    chat_send_db.title, chat_send_db.cost, user_db.bfly))
                state = dp.current_state(chat=user_db.userid, user=user_db.userid)
                async with state.proxy() as data:
                    data["to_chat_id"] = chat_send_db.chatid
                    data["del_message"] = msg.message_id
                await Form.message.set()

            else:
                no_money_markup = types.InlineKeyboardMarkup(1)
                no_money_markup.add(types.InlineKeyboardButton(texts[user_db.language]["st_mark_buy"]))
                await bot.send_message(call_user.id, texts[user_db.language]["no_money"], reply_markup=no_money_markup)

    else:
        group_db = ChatDb(msg_chat.id)  # First steps with Classes :)
        await group_db.search_chat()

        # First begin markup ( NOT private chat)
        start_group_mp = types.InlineKeyboardMarkup(1)
        url = "https://t.me/HoodedBot?start={}".format(msg_chat.id)
        st_g_mp_send_msg = types.InlineKeyboardButton(text=texts[user_db.language]["st_g_mp_but"],
                                                      url=url)
        start_group_mp.add(st_g_mp_send_msg)

        await bot.send_message(msg_chat.id, texts[user_db.language]["st_msg_group"].format(
            group_db.cost, group_db.sended), reply_markup=start_group_mp, parse_mode='HTML')


@dp.message_handler(commands='language')
async def cmd_language(message: types.Message):
    if message.chat.type == 'private':
        lang_mar = types.InlineKeyboardMarkup()
        lang_mar.add(types.InlineKeyboardButton("English", callback_data="en"))
        lang_mar.add(types.InlineKeyboardButton("Українська", callback_data="ua"))
        lang_mar.add(types.InlineKeyboardButton("Русский", callback_data="ru"))

        await bot.send_message(message.chat.id, "Choose language:\n"
                                                "Обери мову:\n"
                                                "Выбери язык:", reply_markup=lang_mar)


@dp.message_handler(commands='cost')
async def cmd_start(message: types.Message):

    msg_chat = message.chat

    user_db = UserDb(message.from_user.id)
    if message.chat.type == "private":
        user_chats_markup = types.InlineKeyboardMarkup(1)
        has_chat = False
        async for chat in user_db.find_chats(['creator', 'administrator']):
            has_chat = True
            chat_inf = await bot.get_chat(chat)
            button = types.InlineKeyboardButton(text="{}".format(chat_inf.title),
                                                callback_data='edit cost_{}'.format(chat))
            user_chats_markup.add(button)
        if has_chat:
            await bot.send_message(msg_chat.id, texts[user_db.language]["choose_chatedit"],
                                   reply_markup=user_chats_markup)
        else:
            await bot.send_message(msg_chat.id, texts[user_db.language]["not_admin"])



# Callback handling
@dp.callback_query_handler(lambda call: True)
async def call_back(call):
    time_st = time.time()
    call_chat = call.message.chat
    call_user = call.from_user

    user_db = UserDb(call_user.id)
    await user_db.search_user()

    if call_chat.type == "private":

        if call.data == "send message group":
            user_chats_markup = types.InlineKeyboardMarkup(1)
            has_chat = False
            async for chat in user_db.find_chats(['creator', 'administrator', 'member']):
                has_chat = True
                chat_inf = await bot.get_chat(chat)
                button = types.InlineKeyboardButton(text="{}".format(chat_inf.title),
                                                    callback_data='send message_{}'.format(chat))
                user_chats_markup.add(button)
            if has_chat:
                await bot.send_message(call_chat.id, texts[user_db.language]["choose_chat"],
                                       reply_markup=user_chats_markup)
            else:
                add_bot_chat_markup = types.InlineKeyboardMarkup(1)
                add_bot_chat_but = types.InlineKeyboardButton(text=texts[user_db.language]["add_in_ch_but"],
                                                              url='http://t.me/HoodedBot?startgroup=test')
                add_bot_chat_markup.add(add_bot_chat_but)
                await bot.send_message(call_chat.id, texts[user_db.language]["usr_hasnt_chats"],
                                       reply_markup=add_bot_chat_markup)
            print(time.time() - time_st)

        elif call.data.split("_")[0] == "send message":

            chat_send_db = ChatDb(call.data.split("_")[1])  # Chat for anonim message
            await chat_send_db.search_chat()  # Chat for anonim message

            if chat_send_db.cost <= user_db.bfly:
                await bot.edit_message_text(chat_id=call_chat.id, message_id=call.message.message_id,
                                            text=texts[user_db.language]["before_sending"].format(
                                             chat_send_db.title, chat_send_db.cost, user_db.bfly), reply_markup=None)
                state = dp.current_state(chat=call_chat.id, user=call_user.id)
                async with state.proxy() as data:
                    data["to_chat_id"] = chat_send_db.chatid
                    data["del_message"] = call.message.message_id
                await Form.message.set()

            else:
                no_money_markup = types.InlineKeyboardMarkup(1)
                no_money_markup.add(types.InlineKeyboardButton(texts[user_db.language]["st_mark_buy"], callback_data="buy bfly"))
                await bot.send_message(call_chat.id, texts[user_db.language]["no_money"].format(
                    chat_send_db.cost, user_db.bfly), reply_markup=no_money_markup)

        elif call.data == "send":
            state = dp.current_state(chat=call_chat.id, user=call_user.id)
            async with state.proxy() as data:
                message_id = data["message"]
                from_chat_id = data["from_chat_id"]
                to_chat_id = data["to_chat_id"]
            await state.finish()
            chat_send_db = ChatDb(to_chat_id)
            await chat_send_db.search_chat()
            await chat_send_db.send(from_chat_id, message_id)
            await bot.delete_message(call_chat.id, call.message.message_id)
            await bot.delete_message(call_chat.id, message_id)
            await user_db.edit_bfly("-{}".format(chat_send_db.cost))
            await user_db.search_user()
            await start_msg(call_chat, user_db)


        elif call.data == "send message ls":
            await bot.send_message(call_chat.id, texts[user_db.language]["not_ready"], parse_mode='HTML')
        elif call.data == "buy bfly":
            await bot.send_message(call_chat.id, texts[user_db.language]["not_ready"], parse_mode='HTML')
        elif call.data == "no":
            state = dp.current_state(chat=call_chat.id, user=call_user.id)
            async with state.proxy() as data:
                message_id = data["message"]
            await state.finish()
            await bot.delete_message(call_chat.id, call.message.message_id)
            await bot.delete_message(call_chat.id, message_id)
        elif call.data in ["en", "ru", "ua"]:
            await user_db.edit_lang(call.data)
            await bot.send_message(call_chat.id, texts[call.data]["lang_edited"])
        elif call.data.split("_")[0] == "edit cost":
            chat_edit_db = ChatDb(call.data.split("_")[1])
            await chat_edit_db.search_chat()
            await bot.send_message(call_chat.id, texts[user_db.language]["edit_cost"].format(
                chat_edit_db.title, chat_edit_db.cost))
            state = dp.current_state(chat=call_chat.id, user=call_user.id)
            async with state.proxy() as data:
                data["chat_id"] = chat_edit_db.chatid
            await Cost.new_cost.set()



@dp.message_handler(state=Cost.new_cost)
async def get_message(message: types.Message, state: FSMContext):
    user_db = UserDb(message.from_user.id)
    if message.text.isnumeric():
        async with state.proxy() as data:
            chat_edit_id = data["chat_id"]
        chat_edit_db = ChatDb(chat_edit_id)
        await chat_edit_db.search_chat()
        await chat_edit_db.edit_cost(message.text)
        await bot.send_message(message.chat.id, texts[user_db.language]["cost_edited"])
        await state.finish()
    else:
        await bot.send_message(message.chat.id, texts[user_db.language]["send_numeric"])
        await Cost.new_cost.set()




@dp.message_handler(state=Form.message)
async def get_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await bot.delete_message(message.chat.id, data["del_message"])
        data["from_chat_id"] = message.chat.id
        data["message"] = message.message_id
        chat_to_send = data["to_chat_id"]

    user_db = UserDb(message.from_user.id)
    chat_to_send_db = ChatDb(chat_to_send)
    await chat_to_send_db.search_chat()

    yes_no_markup = types.InlineKeyboardMarkup(1)
    yes_no_markup.add(types.InlineKeyboardButton(text=texts[user_db.language]["yes"], callback_data="send"))
    yes_no_markup.add(types.InlineKeyboardButton(text=texts[user_db.language]["no"], callback_data="no"))
    await state.reset_state(with_data=False)
    await bot.send_message(chat_id=message.chat.id, text=texts[user_db.language]["send_last_q"].format(
        chat_to_send_db.title, chat_to_send_db.cost), reply_markup=yes_no_markup)
    await state.reset_state(with_data=False)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
