import traceback
import psycopg2
import telebot
from telebot import types
import datetime
from config import *

# Create var for bot
bot = telebot.TeleBot(token_id)

# establishing the connection to DB
conn = psycopg2.connect(
    database=namedb, user=user, password=password, host=host, port=port
)
conn.autocommit = True


def add_new_user(message):
    try:
        chat_id = message.chat.id
        user_name = '@' + str(message.chat.username)
        date = datetime.datetime.now()
        first_name = message.chat.first_name
        last_name = message.chat.last_name
        role = 'user'
        with conn.cursor() as cursor:
            entry = (chat_id, first_name, last_name, user_name, date, role)
            cursor.execute(
                '''INSERT INTO users (chat_id, first_name, last_name, username, reg_date, role) VALUES
                 (%s, %s, %s, %s, %s, %s);''', entry
            )
    except Exception:
        pass


def add_log_users(message):
    chat_id = message.chat.id
    username = '@' + str(message.chat.username)
    message_text = message.text
    first_name = message.chat.first_name
    last_name = message.chat.last_name
    date = datetime.datetime.now()
    with conn.cursor() as cursor:
        entry = (chat_id, username, first_name, last_name, message_text, date)
        cursor.execute(
            '''INSERT INTO log_users (chat_id,username, first_name, last_name, message_text, date) VALUES
             (%s, %s, %s, %s, %s, %s);''', entry
        )


def get_user_role(message):
    chat_id = message.chat.id
    with conn.cursor() as cursor:
        cursor.execute(
            '''SELECT role FROM users WHERE chat_id = %s;''', [chat_id])
        return str(cursor.fetchone()[0])


def get_count_today(message):
    chat_id = message.chat.id
    date = datetime.datetime.now()
    entry = (chat_id, date.day, date.month, date.year, date.hour)
    with conn.cursor() as cursor:
        cursor.execute(
            '''SELECT COUNT(*) 
            FROM log_users 
            WHERE chat_id = %s AND 
            EXTRACT(DAY FROM date) = %s AND
            EXTRACT(MONTH FROM date) = %s AND
            EXTRACT(YEAR FROM date) = %s AND 
            EXTRACT(HOUR FROM date) = %s;''', entry)
        return int(cursor.fetchone()[0])


def get_count_orders():
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                '''SELECT order_id FROM orders ORDER BY order_id DESC LIMIT 1;''')
            return int(cursor.fetchone()[0])
    except TypeError:
        return 0


def save_order(data):
    with conn.cursor() as cursor:
        entry = tuple(data.values())
        cursor.execute(
            '''INSERT INTO orders (order_id,item_id, price, price_rub, size, date, chat_id, username,status) VALUES
             (%s, %s, %s, %s, %s, %s, %s, %s, %s);''', entry
        )


@bot.message_handler(content_types='text')
def main_menu(message):
    add_new_user(message)
    add_log_users(message)
    role = get_user_role(message)
    if role not in 'admin' and role not in 'banned':
        if get_count_today(message) > 2:
            help_message = '''
Если у вас есть вопросы, то мы всегда рады помочь!
            
Помощь с выбором размера и просто любые вопросы:
@kiiroiashi, @studisram

Техническая поддержка бота:
@SpiritPower.
            '''
            bot.send_message(message.from_user.id, help_message)
        start_menu(message)
    elif role in 'admin':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        menu = types.KeyboardButton('Вернуться в меню пользователя')
        admin_menu = types.KeyboardButton('Админское меню')
        markup.add(menu, admin_menu)
        msg = bot.send_message(message.chat.id, 'Администратор', reply_markup=markup)
        bot.register_next_step_handler(msg, func)
    else:
        bot.send_message(message.from_user.id, 'Вы забанены')


def start_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    calculator = types.KeyboardButton('Рассчитать стоимость')
    order_item = types.KeyboardButton('Создать заказ')
    faq = types.KeyboardButton('FAQ')
    reviews = types.KeyboardButton('Отзывы')
    history = types.KeyboardButton('История заказов')
    markup.add(calculator, order_item, faq, reviews, history)
    msg = bot.send_message(message.chat.id, 'Главное меню', reply_markup=markup)
    bot.register_next_step_handler(msg, func)


def func(message):
    if message.text == "Создать заказ":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_main_menu = types.KeyboardButton('Вернуться в главное меню')
        markup.add(back_main_menu)
        bot.send_message(message.from_user.id, 'Заказ товара', reply_markup=markup)
        order(message)
    elif message.text == "Вернуться в меню пользователя":
        start_menu(message)
    elif message.text == "Рассчитать стоимость":

        markup = types.InlineKeyboardMarkup()

        faq = types.InlineKeyboardButton("Как считается стоимость?",
                                         url='https://telegra.ph/Raschyot-stoimosti-09-14-2')
        markup.add(faq)
        msg = bot.send_message(message.chat.id, 'Введите стоимость', reply_markup=markup)
        bot.register_next_step_handler(msg, calculate_reply)
    elif message.text == "FAQ":
        bot.send_message(message.chat.id, text='''
        Ответы на часто задаваемые вопросы:


 *1. Можно ли заказать два товара и поделить оплату за доставку?* 

Ответ: конечно да. Цена за доставку рассчитывается 1000р/1кг

 *2. Как проходит оплата?* 

Ответ: 100% предоплата

 *3. Что если не подойдёт размер? А можно заказать несколько с примеркой?* 

Ответ: Друзья, мы помогаем вам экономить деньги на заказе одежды/обуви. Мы поможем вам подобрать размер и сделаем все что в наших силах, но учитывать особенности ноги каждого человека мы не можем. Вы можете померить эту же пару в офлайн магазине чтобы быть уверенным в правильности размера.

 *4. Это не оригинал/копия?* 

Ответ: Нет! Мы предоставляем СТРОГО ОРИГИНАЛЬНУЮ ПРОДУКЦИЮ.
Все товары проходят через особую процедуру проверки на оригинальность от самого сервиса POIZON, а только потом передаются в службу доставки.

 *5. Сколько по времени идёт товар?* 

Ответ: Доставка товара занимает от 3 недель до месяца''', parse_mode='Markdown')
        main_menu(message)

    elif message.text == "Отзывы":
        bot.send_message(message.chat.id, text="Наши отзывы: https://t.me/FFfeedbacksneakers")
        main_menu(message)
    elif message.text == "История заказов":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_main_menu = types.KeyboardButton('Вернуться в главное меню')
        markup.add(back_main_menu)
        bot.send_message(message.from_user.id, 'История ваших заказов:', reply_markup=markup)
        order_history(message)
    elif message.text == 'Админское меню':
        role = get_user_role(message)
        if role in 'admin':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            update = types.KeyboardButton("Обновить заказ")
            ban_user = types.KeyboardButton("Забанить пользователя")
            unban_user = types.KeyboardButton("Разбанить пользователя")
            add_admin = types.KeyboardButton("Добавить админа")
            delete_admin = types.KeyboardButton("Удалить админа")
            delete_order = types.KeyboardButton("Удалить заказ")
            back_main_menu = types.KeyboardButton("Вернуться в главное меню")
            cny = types.KeyboardButton("Обновить курс ¥")
            markup.add(back_main_menu, update, cny, delete_order, ban_user, unban_user, add_admin, delete_admin)
            msg = bot.send_message(message.chat.id, 'Что необходимо сделать?', reply_markup=markup)
            bot.register_next_step_handler(msg, admin_func)
        else:
            bot_error(message)
    else:
        bot_error(message)


def admin_func(message):
    if message.text == "Обновить заказ":
        with conn.cursor() as cursor:
            cursor.execute(
                '''SELECT order_id FROM orders WHERE status <> 'Заказ доставлен' ORDER BY order_id;''')
            data = (cursor.fetchall())
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for order in data:
            button = types.KeyboardButton(order[0])
            markup.add(button)
        msg = bot.send_message(message.chat.id, 'Введите номер заказа:', reply_markup=markup)
        bot.register_next_step_handler(msg, update_order_details)
    elif message.text == "Забанить пользователя":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        msg = bot.send_message(message.chat.id, 'Введите ссылку на пользователя (tg://user?id=):',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, change_role, 'banned')
    elif message.text == "Разбанить пользователя":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        msg = bot.send_message(message.chat.id, 'Введите ссылку на пользователя (tg://user?id=):',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, change_role, 'user')
    elif message.text == "Добавить админа":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        msg = bot.send_message(message.chat.id, 'Введите ссылку на пользователя (tg://user?id=):',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, change_role, 'admin')
    elif message.text == "Удалить админа":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        msg = bot.send_message(message.chat.id, 'Введите ссылку на пользователя (tg://user?id=):',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, change_role, 'user')
    elif message.text == "Удалить заказ":
        with conn.cursor() as cursor:
            cursor.execute(
                '''SELECT order_id FROM orders;''')
            data = (cursor.fetchall())
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for order in data:
            button = types.KeyboardButton(order[0])
            markup.add(button)
        msg = bot.send_message(message.chat.id, 'Введите номер заказа:', reply_markup=markup)
        bot.register_next_step_handler(msg, remove_order)
    elif message.text == "Обновить курс ¥":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        msg = bot.send_message(message.chat.id, 'Введите новый курс ¥:',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, update_cny)
    elif message.text == "Вернуться в главное меню":
        main_menu(message)
    else:
        bot_error(message)


def remove_order(message):
    if message.text == "Вернуться в главное меню":
        main_menu(message)
    else:
        with conn.cursor() as cursor:
            cursor.execute(
                '''DELETE FROM orders 
                WHERE order_id = %s 
                RETURNING chat_id,order_id;''', [message.text])
            chat_id, order_id = cursor.fetchone()
        bot.send_message(message.chat.id, f'Заказ {order_id} удален')
        bot.send_message(chat_id, f'''Ваш заказ {order_id} удален''')
        main_menu(message)


def change_role(message, role):
    try:
        user_id = int(message.text.split('tg://user?id=')[-1])
        entry = (role, user_id)
        with conn.cursor() as cursor:
            cursor.execute(
                '''UPDATE users 
                SET role = %s 
                WHERE chat_id = %s;''', entry)
        bot.send_message(message.chat.id, f'Роль пользователя {user_id} изменена на {role}')
        main_menu(message)
    except Exception:
        bot_error(message)


def update_cny(message):
    try:
        price = float(message.text)
        chat_id = message.chat.id
        username = '@' + str(message.chat.username)
        date = datetime.datetime.now()

        with conn.cursor() as cursor:
            entry = (price, username, chat_id, date)
            cursor.execute(
                '''INSERT INTO cny_price (price,username,chat_id,date) VALUES
                 (%s, %s, %s, %s);''', entry
            )
        bot.send_message(message.chat.id, f'Курс изменен на 1¥ - {price}₽')
        main_menu(message)
    except TypeError:
        bot_error(message)


def update_order_details(message):
    order_id = message.text
    bot.send_message(message.chat.id, f'Вы выбрали {message.text} заказ')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    item_id = types.KeyboardButton("Артикул")
    price = types.KeyboardButton("Цена в ¥")
    price_rub = types.KeyboardButton("Цена в ₽")
    size = types.KeyboardButton("Размер")
    status = types.KeyboardButton("Статус")
    back_button = types.KeyboardButton("Вернуться в главное меню")
    markup.add(item_id, price, price_rub, size, status, back_button)
    msg = bot.send_message(message.chat.id, 'Что необходимо изменить?', reply_markup=markup)
    bot.register_next_step_handler(msg, update_order, order_id)


def update_order(message, order_id):
    if message.text == "Вернуться в главное меню":
        main_menu(message)
    elif message.text == 'Артикул':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_main_menu = types.KeyboardButton("Вернуться в главное меню")
        markup.add(back_main_menu)
        change_what_str = message.text
        change_what = 'item_id'
        msg = bot.send_message(message.chat.id, f'Как изменить {change_what_str.lower()}?', reply_markup=markup)
        bot.register_next_step_handler(msg, update_order_info, order_id, change_what, change_what_str)
    elif message.text == 'Цена в ¥':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_main_menu = types.KeyboardButton("Вернуться в главное меню")
        markup.add(back_main_menu)
        change_what_str = message.text
        change_what = 'price'
        msg = bot.send_message(message.chat.id, f'Как изменить {change_what_str.lower()}?', reply_markup=markup)
        bot.register_next_step_handler(msg, update_order_info, order_id, change_what, change_what_str)
    elif message.text == 'Цена в ₽':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_main_menu = types.KeyboardButton("Вернуться в главное меню")
        markup.add(back_main_menu)
        change_what_str = message.text
        change_what = 'price_rub'
        msg = bot.send_message(message.chat.id, f'Как изменить {change_what_str.lower()}?', reply_markup=markup)
        bot.register_next_step_handler(msg, update_order_info, order_id, change_what, change_what_str)
    elif message.text == 'Размер':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        back_main_menu = types.KeyboardButton("Вернуться в главное меню")
        markup.add(back_main_menu)
        change_what_str = message.text
        change_what = 'size'
        msg = bot.send_message(message.chat.id, f'Как изменить {change_what_str.lower()}?', reply_markup=markup)
        bot.register_next_step_handler(msg, update_order_info, order_id, change_what, change_what_str)
    elif message.text == 'Статус':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        order_waiting = types.KeyboardButton("Ожидание подтверждения оператора")
        order_confirmed = types.KeyboardButton("Заказ подтвержден")
        order_sent = types.KeyboardButton("Заказ отправлен с Poizon")
        order_russia_arrived = types.KeyboardButton("Заказ прибыл в Москву")
        order_russia_sent = types.KeyboardButton("Заказ отправлен доставкой в Москве")
        order_received = types.KeyboardButton("Заказ доставлен")
        back_main_menu = types.KeyboardButton("Вернуться в главное меню")
        markup.add(order_waiting, order_confirmed, order_sent, order_russia_arrived, order_russia_sent,
                   order_received, back_main_menu)
        change_what_str = message.text
        change_what = 'status'
        msg = bot.send_message(message.chat.id, f'Как изменить {change_what_str.lower()}?', reply_markup=markup)
        bot.register_next_step_handler(msg, update_order_info, order_id, change_what, change_what_str)


def update_order_info(message, order_id, change_what, change_what_str):
    if message.text == "Вернуться в главное меню":
        main_menu(message)
    else:
        try:
            entry = (message.text, order_id)
            with conn.cursor() as cursor:
                cursor.execute(
                    f'''UPDATE orders 
                    SET {change_what} = %s 
                    WHERE order_id = %s 
                    RETURNING chat_id;''', entry)
                user_id = cursor.fetchone()[0]
            bot.send_message(message.chat.id,
                             f'{change_what_str} заказа {order_id} изменен на - {message.text}')
            bot.send_message(user_id, f'''
Заказ {order_id}  - изменен "{change_what_str.lower()}" на:
{message.text}''')
            main_menu(message)
        except Exception:
            bot_error(message)


def calculate(message):
    try:
        orig_price = int(message.text)
        if orig_price > 0:  # if input price is int and > 0 calculate prefinal price for product
            poizon_fee = 20  # poizon fee in CNY
            ff_fee = 1500  # fee FF in RUB
            with conn.cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT price
                    FROM cny_price 
                    ORDER BY date DESC 
                    LIMIT 1;''')
                cny_price = cursor.fetchone()[0]
            prefinal_price = (orig_price + poizon_fee) * cny_price + ff_fee
            return int(prefinal_price)
        else:
            return 0

    except Exception:
        return 0


def calculate_reply(message):
    try:
        bot.send_message(message.chat.id, text=f"Цена без учета доставки в рублях: {calculate(message)}₽")

    except:
        bot.send_message(message.chat.id, text=f"Цена без учета доставки в рублях: {0}₽")

    main_menu(message)


def order(message):
    data = {}
    data['order_id'] = get_count_orders() + 1
    markup = types.InlineKeyboardMarkup()
    faq = types.InlineKeyboardButton("Как правильно оформить заказ?",
                                     url='https://telegra.ph/Kak-pravilno-oformit-zakaz-09-13')
    markup.add(faq)
    msg = bot.send_message(message.chat.id, 'Введите артикул (主货号):', reply_markup=markup)
    bot.register_next_step_handler(msg, order_price, data)


def order_price(message, data):
    if message.text == 'Вернуться в главное меню':
        main_menu(message)
        return
    data['item_id'] = message.text  # Poizon item id input from user
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Как правильно оформить заказ?",
                                          url='https://telegra.ph/Kak-pravilno-oformit-zakaz-09-13'))
    msg = bot.send_message(message.chat.id, 'Введите цену в Юанях (¥):', reply_markup=markup)
    bot.register_next_step_handler(msg, order_size, data)


def order_size(message, data):
    if message.text == 'Вернуться в главное меню':
        main_menu(message)
        return
    try:
        price = int(str(message.text))
    except:
        price = 0
    data['price'] = price  # price CNY input from user
    data['price_rub'] = calculate(message)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Как правильно оформить заказ?",
                                          url='https://telegra.ph/Kak-pravilno-oformit-zakaz-09-13'))

    msg = bot.send_message(message.chat.id, 'Введите размер (EU/US/CM):', reply_markup=markup)
    bot.register_next_step_handler(msg, order_data, data)


def order_data(message, data):
    if message.text == 'Вернуться в главное меню':
        main_menu(message)
        return
    data['size'] = message.text  # size input from user
    # get date
    data['date'] = datetime.datetime.now()
    markup = types.InlineKeyboardMarkup()
    order_data = f'''
    Проверка заказа:
Артикул: {data['item_id']}
Цена в юанях: {data['price']}¥
Цена в рублях (без учета доставки): {data['price_rub']}₽
Размер: {data['size']}'''

    bot.send_message(message.chat.id, order_data, reply_markup=markup)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    yes = types.KeyboardButton('Да')
    no = types.KeyboardButton('Нет')
    markup.add(yes, no)
    msg = bot.send_message(message.chat.id, 'Подтвердить заказ?', reply_markup=markup)
    bot.register_next_step_handler(msg, order_confirm, data)


def order_confirm(message, data):
    if message.text == 'Вернуться в главное меню':
        main_menu(message)
        return
    if message.text.lower() == 'да':
        chat_id = order_chat_id  # id of orders chat
        data['chat_id'] = message.chat.id
        data['username'] = '@' + str(message.chat.username)
        data['status'] = 'Ожидание подтверждения оператора'
        save_order(data)  # add order to SQL orders
        send = f'''
Дата заказа: {data['date'].strftime("%d/%m/%Y, %H:%M:%S")}
Номер заказа: {data['order_id']}
Артикул: {data['item_id']}
Цена в юанях: {data['price']}¥
Цена в рублях (без учета доставки): {data['price_rub']}₽
Размер: {data['size']}
Статус: {data['status']}
Ник: @{message.chat.username}
Telegram id: tg://user?id={data['chat_id']}'''
        bot.send_message(chat_id, send)

        bot.send_message(message.chat.id, f'''
Номер вашего заказа: {data['order_id']}
Наши операторы с вами свяжутся :)
        ''')
        main_menu(message)
    else:
        message.text = f'''Артикул: {data['item_id']}
Цена в юанях: {data['price']}¥
Цена в рублях (без учета доставки): {data['price_rub']}₽
Размер: {data['size']}'''
        main_menu(message)


def order_history(message):
    with conn.cursor() as cursor:
        entry = message.chat.id
        cursor.execute(
            '''
            SELECT * FROM orders 
            WHERE chat_id = %s 
            ORDER BY order_id;''', [entry])
        data = (cursor.fetchall())
    for order in data:
        item_id = order[1]
        price = order[2]
        price_rub = order[3]
        size = order[4]
        day = order[5]
        order_id = order[0]
        status = order[8]
        bot.send_message(message.chat.id, f'''
Дата заказа: {day.strftime("%d/%m/%Y, %H:%M:%S")}
Номер заказа: {order_id}
Статус заказа: {status}
Артикул: {item_id}
Цена в юанях: {price}¥
Цена в рублях (без учета доставки): {price_rub}₽
Размер: {size} ''')
    main_menu(message)


def bot_error(message):
    bot.send_message(message.chat.id, text="Неправильный запрос")
    main_menu(message)


def telegram_polling():
    try:
        bot.polling(none_stop=True, timeout=60)  # constantly get messages from Telegram
    except Exception:
        traceback_error_string = traceback.format_exc()
        with open("Error.Log", "a") as myfile:
            date = str(datetime.datetime.now())
            myfile.write(
                "\r\n\r\n" + date + "  " + "\r\n<<ERROR polling>>\r\n" + traceback_error_string + "\r\n<<ERROR polling>>")
        bot.stop_polling()
        telegram_polling()


if __name__ == '__main__':
    telegram_polling()
    bot.polling(none_stop=True, timeout=60)
