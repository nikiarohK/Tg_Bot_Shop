from config import BOT_TOKEN
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Chat
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_categories, get_products_by_category, get_product, initialize_database
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Хранилище данных пользователей
user_data = {}

# Состояния для FSM
class Form(StatesGroup):
    waiting_for_phone_choice = State()
    waiting_for_phone_manual = State()
    waiting_for_address = State()

def get_main_keyboard():
    """Создает главную клавиатуру"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Каталог"))
    builder.row(
        KeyboardButton(text="Корзина"),
        KeyboardButton(text="Доставка")
    )
    builder.row(
        KeyboardButton(text="Онлайн-чат"),
        KeyboardButton(text="Позвонить")
    )
    return builder.as_markup(resize_keyboard=True)

async def update_main_message(chat_id: int, user_id: int, text: str = "Главное меню"):
    """Обновляет главное сообщение с клавиатурой"""
    if user_id not in user_data:
        user_data[user_id] = {'main_message_id': None, 'other_messages': [], 'cart': {}}
    
    if user_data[user_id]['main_message_id']:
        try:
            await bot.delete_message(chat_id, user_data[user_id]['main_message_id'])
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")
    
    sent_message = await bot.send_message(
        chat_id,
        text,
        reply_markup=get_main_keyboard()
    )
    user_data[user_id]['main_message_id'] = sent_message.message_id
    return sent_message

async def clean_other_messages(chat_id: int, user_id: int):
    """Удаляет все сообщения кроме главного"""
    if user_id in user_data and 'other_messages' in user_data[user_id]:
        for msg_id in user_data[user_id]['other_messages']:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения: {e}")
        user_data[user_id]['other_messages'] = []

async def delete_user_message(message: types.Message):
    """Пытается удалить сообщение пользователя"""
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await update_main_message(chat_id, user_id, "Добро пожаловать в наш магазин!")
    await clean_other_messages(chat_id, user_id)
    await delete_user_message(message)

@dp.message(F.text == "Каталог")
async def show_catalog_menu(message: types.Message):
    """Показ меню каталога"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    await delete_user_message(message)
    
    categories = get_categories()
    builder = InlineKeyboardBuilder()
    for category_id, category_name in categories.items():
        builder.add(InlineKeyboardButton(
            text=category_name,
            callback_data=f"category_{category_id}"
        ))
    builder.adjust(2)
    
    sent_message = await bot.send_message(
        chat_id,
        "Выберите категорию товаров:",
        reply_markup=builder.as_markup()
    )
    user_data[user_id]['other_messages'].append(sent_message.message_id)

@dp.message(F.text == "Доставка")
async def show_delivery_info(message: types.Message):
    """Информация о доставке"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    await delete_user_message(message)
    
    delivery_text = (
        "Доставка в пределах МКАД 0 рублей!\n\n"
        "Доставка от 15 минут!\n\n"
        "Минимальная сумма заказа от 400 рублей!\n\n"
        "ОПЛАТА наличными, переводом, по факту получения заказа!\n\n"
        "КУРЬЕР МОЖЕТ ПОПРОСИТЬ ПЕРЕВОД ЗАРАНЕЕ, ЕСЛИ ЗАКАЗЫВАЕТЕ ПЕРВЫЙ РАЗ ЧЕРЕЗ НАШ БОТ!"
    )
    
    sent_message = await bot.send_message(chat_id, delivery_text)
    user_data[user_id]['other_messages'].append(sent_message.message_id)

@dp.message(F.text == "Позвонить")
async def show_phone_number(message: types.Message):
    """Показ номера телефона"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    await delete_user_message(message)
    
    sent_message = await bot.send_message(
        chat_id,
        "Чтобы связаться с оператором, позвоните:\n<b>+7 (499) 350-84-17</b>"
    )
    user_data[user_id]['other_messages'].append(sent_message.message_id)

@dp.message(F.text == "Онлайн-чат")
async def show_online_chat(message: types.Message):
    """Ссылка на онлайн-чат"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    await delete_user_message(message)
    
    sent_message = await bot.send_message(chat_id, "Перейдите в чат с оператором: @nikiarohk")
    user_data[user_id]['other_messages'].append(sent_message.message_id)

@dp.message(F.text == "Корзина")
async def show_cart(message: types.Message):
    """Показ корзины с товарами и общей суммой"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    await delete_user_message(message)
    
    if not user_data.get(user_id, {}).get('cart'):
        sent_message = await bot.send_message(chat_id, "Корзина пуста")
        user_data[user_id]['other_messages'].append(sent_message.message_id)
        return
    
    # Формируем текст корзины
    cart_text = "Сейчас в Вашей корзине:\n\n"
    total = 0
    
    for product_id, quantity in user_data[user_id]['cart'].items():
        product = get_product(product_id)
        if product:
            product_total = quantity * product['price']
            cart_text += f"{product['name']}: {product['price']} Руб x {quantity}\n"
            total += product_total
    
    cart_text += f"\nСумма без доставки: {total} Руб"
    
    # Создаем инлайн-клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Редактировать", callback_data="edit_cart"),
            InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")
        ]
    ])
    
    sent_message = await bot.send_message(
        chat_id,
        cart_text,
        reply_markup=keyboard
    )
    user_data[user_id]['other_messages'].append(sent_message.message_id)

@dp.callback_query(F.data == "edit_cart")
async def edit_cart(callback: types.CallbackQuery):
    """Обработчик кнопки Редактировать с отображением количества"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    if not user_data.get(user_id, {}).get('cart'):
        await callback.answer("Корзина пуста")
        return
    
    # Удаляем предыдущее сообщение
    try:
        await bot.delete_message(chat_id=chat_id, message_id=callback.message.message_id)
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")
    
    # Создаем клавиатуру с товарами для редактирования
    builder = InlineKeyboardBuilder()
    
    for product_id, quantity in user_data[user_id]['cart'].items():
        product = get_product(product_id)
        if product:
            builder.add(InlineKeyboardButton(
                text=f"{product['name']} ({quantity})",  # Добавляем количество в скобках
                callback_data=f"edit_item_{product_id}"
            ))
    
    builder.adjust(1)
    
    # Добавляем кнопку "Назад"
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_cart_from_edit"
    ))
    
    sent_message = await bot.send_message(
        chat_id,
        "Выберите товар, который нужно изменить:",
        reply_markup=builder.as_markup()
    )
    user_data[user_id]['other_messages'].append(sent_message.message_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_item_"))
async def edit_item(callback: types.CallbackQuery):
    """Отображение товара с фото и кнопками редактирования"""
    try:
        product_id = int(callback.data.split("_")[2])
    except IndexError:
        product_id = int(callback.data.split("_")[1])
    
    product = get_product(product_id)
    user_id = callback.from_user.id
    
    if not product or user_id not in user_data or product_id not in user_data[user_id]['cart']:
        await callback.answer("Товар не найден")
        return
    
    quantity = user_data[user_id]['cart'][product_id]
    total_price = quantity * product['price']
    
    # Формируем текст сообщения
    text = (
        f"Просмотр товара в категории: {get_categories().get(product['category'], 'Без категории')}\n\n"
        f"<b>{product['name']}</b>\n\n"
        f"Цена: {product['price']} Руб.\n"
        f"Количество: {quantity}\n"
        f"Итого: {total_price} Руб."
    )
    
    # Создаем клавиатуру для редактирования с новой структурой
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Первая строка: цена * количество = итоговая цена
        [
            InlineKeyboardButton(
                text=f"{product['price']} Руб × {quantity} = {total_price} Руб", 
                callback_data="no_action"
            )
        ],
        # Вторая строка: кнопки - + Удалить
        [
            InlineKeyboardButton(text="-", callback_data=f"dec_item_{product_id}"),
            InlineKeyboardButton(text="+", callback_data=f"inc_item_{product_id}"),
            InlineKeyboardButton(text="Удалить", callback_data=f"del_item_{product_id}")
        ],
        # Третья строка: Оформить заказ
        [
            InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")
        ],
        # Четвертая строка: Сохранить и вернуться в корзину
        [
            InlineKeyboardButton(text="Сохранить и вернуться в корзину", callback_data="back_to_cart_from_edit")
        ]
    ])
    
    try:
        # Проверяем, есть ли фото товара
        image_path = product.get('image_url')
        
        # Если это первое открытие товара (не редактирование)
        if not callback.message.photo and image_path and os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await callback.message.delete()
            sent_message = await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=photo,
                caption=text,
                reply_markup=keyboard
            )
            # Сохраняем ID сообщения
            if user_id not in user_data:
                user_data[user_id] = {'main_message_id': None, 'other_messages': [], 'cart': {}}
            user_data[user_id]['other_messages'].append(sent_message.message_id)
        else:
            # Если сообщение уже содержит фото - редактируем только подпись
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                # Если фото нет - редактируем текст сообщения
                await callback.message.edit_text(
                    text=text,
                    reply_markup=keyboard
                )
    except Exception as e:
        logger.error(f"Ошибка при отображении товара: {e}")
        await callback.answer("Произошла ошибка при отображении товара")
    finally:
        await callback.answer()

@dp.callback_query(F.data == "back_to_cart_from_edit")
async def back_to_cart_from_edit(callback: types.CallbackQuery):
    """Обработчик кнопки 'Вернуться в корзину' из режима редактирования"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    # Удаляем текущее сообщение с редактированием товара
    try:
        await bot.delete_message(chat_id=chat_id, message_id=callback.message.message_id)
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")
    
    # Создаем временное сообщение для вызова show_cart
    fake_message = types.Message(
        message_id=0,
        date=0,
        chat=Chat(id=chat_id, type="private"),
        from_user=callback.from_user,
        text=""
    )
    await show_cart(fake_message)
    await callback.answer()

@dp.callback_query(F.data.startswith("dec_item_"))
async def decrease_product(callback: types.CallbackQuery):
    """Уменьшение количества товара"""
    try:
        product_id = int(callback.data.split("_")[2])
    except IndexError:
        product_id = int(callback.data.split("_")[1])
    
    user_id = callback.from_user.id
    
    if user_id in user_data and 'cart' in user_data[user_id]:
        if product_id in user_data[user_id]['cart']:
            if user_data[user_id]['cart'][product_id] > 1:
                user_data[user_id]['cart'][product_id] -= 1
                await edit_item(callback)
            else:
                del user_data[user_id]['cart'][product_id]
                await callback.answer("Товар удален")
                await back_to_edit_cart(callback)
    
    await callback.answer()

@dp.callback_query(F.data.startswith("inc_item_"))
async def increase_product(callback: types.CallbackQuery):
    """Увеличение количества товара"""
    try:
        product_id = int(callback.data.split("_")[2])
    except IndexError:
        product_id = int(callback.data.split("_")[1])
    
    user_id = callback.from_user.id
    
    if user_id in user_data and 'cart' in user_data[user_id]:
        if product_id in user_data[user_id]['cart']:
            user_data[user_id]['cart'][product_id] += 1
            await edit_item(callback)
    
    await callback.answer()

@dp.callback_query(F.data.startswith("del_item_"))
async def remove_product(callback: types.CallbackQuery):
    """Полное удаление товара из корзины"""
    try:
        product_id = int(callback.data.split("_")[2])
    except IndexError:
        product_id = int(callback.data.split("_")[1])
    
    user_id = callback.from_user.id
    
    if user_id in user_data and 'cart' in user_data[user_id]:
        if product_id in user_data[user_id]['cart']:
            del user_data[user_id]['cart'][product_id]
            await callback.answer("Товар удален")
            await back_to_edit_cart(callback)
    
    await callback.answer()
    
async def refresh_cart_message(callback: types.CallbackQuery):
    """Обновляет сообщение с корзиной"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    if user_id not in user_data or 'cart' not in user_data[user_id] or not user_data[user_id]['cart']:
        await callback.message.edit_text("Ваша корзина пуста!")
        return
    
    cart_text = "Ваша корзина:\n\n"
    total = 0
    for product_id, quantity in user_data[user_id]['cart'].items():
        product = get_product(product_id)
        if product:
            cart_text += f"{product['name']} - {quantity} шт. x {product['price']}₽ = {quantity * product['price']}₽\n"
            total += quantity * product['price']
    
    cart_text += f"\nИтого: {total}₽"
    
    builder = InlineKeyboardBuilder()
    
    for product_id in user_data[user_id]['cart'].keys():
        product = get_product(product_id)
        if product:
            builder.row(
                InlineKeyboardButton(
                    text=f"- {product['name']}",
                    callback_data=f"cart_decrease_{product_id}"
                ),
                InlineKeyboardButton(
                    text=f"+ {product['name']}",
                    callback_data=f"cart_increase_{product_id}"
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text=f"Удалить {product['name']}",
                    callback_data=f"cart_remove_{product_id}"
                )
            )
    
    builder.row(
        InlineKeyboardButton(
            text="Оформить заказ",
            callback_data="checkout"
        ),
        InlineKeyboardButton(
            text="Очистить корзину",
            callback_data="clear_cart"
        )
    )
    
    try:
        await callback.message.edit_text(
            text=cart_text,
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении корзины: {e}")
        await callback.answer("Произошла ошибка при обновлении корзины")

@dp.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: types.CallbackQuery):
    """Показ товаров в категории"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    
    category_id = callback.data.split("_")[1]
    categories = get_categories()
    category_name = categories.get(category_id, "Неизвестная категория")
    category_products = get_products_by_category(category_id)
    
    if not category_products:
        await callback.answer("В этой категории пока нет товаров")
        return
    
    builder = InlineKeyboardBuilder()
    for product_id, product in category_products.items():
        builder.add(InlineKeyboardButton(
            text=f"{product['name']} - {product['price']}₽",
            callback_data=f"product_{product_id}"
        ))
    builder.adjust(1)
    builder.row(InlineKeyboardButton(
        text="Назад к категориям",
        callback_data="back_to_categories"
    ))
    
    sent_message = await bot.send_message(
        chat_id,
        f"Товары в категории <b>{category_name}</b>:",
        reply_markup=builder.as_markup()
    )
    user_data[user_id]['other_messages'].append(sent_message.message_id)
    await callback.answer()

@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery):
    """Возврат к списку категорий"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    
    categories = get_categories()
    builder = InlineKeyboardBuilder()
    for category_id, category_name in categories.items():
        builder.add(InlineKeyboardButton(
            text=category_name,
            callback_data=f"category_{category_id}"
        ))
    builder.adjust(2)
    
    sent_message = await bot.send_message(
        chat_id,
        "Выберите категорию товаров:",
        reply_markup=builder.as_markup()
    )
    user_data[user_id]['other_messages'].append(sent_message.message_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("product_"))
async def show_product(callback: types.CallbackQuery):
    """Показ информации о товаре"""
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[1])
    product = get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден")
        return
    
    current_quantity = user_data[user_id].get('cart', {}).get(product_id, 0)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="-", callback_data=f"decrease_{product_id}"),
            InlineKeyboardButton(text=str(current_quantity), callback_data="no_action"), 
            InlineKeyboardButton(text="+", callback_data=f"increase_{product_id}")
        ],
        [InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add_{product_id}")],
        [
            InlineKeyboardButton(text="Добавили? Оформляем заказ?", callback_data="checkout")
        ],
        [InlineKeyboardButton(text="... или продолжить покупки?", callback_data="continue_shopping")],
        [InlineKeyboardButton(text="Назад", callback_data=f"category_{product['category']}")]
    ])
    
    image_path = product.get('image_url')
    
    try:
        if image_path and os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await callback.message.delete()
            sent_message = await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=photo,
                caption=f"<b>{product['name']}</b>\n\nЦена: {product['price']}₽",
                reply_markup=keyboard
            )
        else:
            await callback.message.delete()
            sent_message = await bot.send_message(
                chat_id=callback.message.chat.id,
                text=f"<b>{product['name']}</b>\n\nЦена: {product['price']}₽",
                reply_markup=keyboard
            )
        
        if user_id not in user_data:
            user_data[user_id] = {'main_message_id': None, 'other_messages': [], 'cart': {}}
        user_data[user_id]['other_messages'].append(sent_message.message_id)
    except Exception as e:
        logger.error(f"Ошибка при отправке товара: {e}")
        await callback.answer("Произошла ошибка при отображении товара")
    finally:
        await callback.answer()

@dp.callback_query(F.data == "continue_shopping")
async def continue_shopping(callback: types.CallbackQuery):
    """Обработчик кнопки 'Продолжить покупки'"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    
    categories = get_categories()
    builder = InlineKeyboardBuilder()
    for category_id, category_name in categories.items():
        builder.add(InlineKeyboardButton(
            text=category_name,
            callback_data=f"category_{category_id}"
        ))
    builder.adjust(2)
    
    sent_message = await bot.send_message(
        chat_id,
        "Выберите категорию товаров:",
        reply_markup=builder.as_markup()
    )
    user_data[user_id]['other_messages'].append(sent_message.message_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    """Добавление товара в корзину (начинается с 1)"""
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[1])
    
    if user_id not in user_data:
        user_data[user_id] = {'main_message_id': None, 'other_messages': [], 'cart': {}}
    
    if 'cart' not in user_data[user_id]:
        user_data[user_id]['cart'] = {}
    
    # Добавляем товар с количеством 1 (вместо увеличения на 1)
    if product_id not in user_data[user_id]['cart']:
        user_data[user_id]['cart'][product_id] = 1
    
    await callback.answer(f"Товар добавлен в корзину! Текущее количество: {user_data[user_id]['cart'][product_id]}")
    
    # Обновляем сообщение с товаром, чтобы счетчик отобразил 1
    product = get_product(product_id)
    if product:
        current_quantity = user_data[user_id]['cart'].get(product_id, 0)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="-", callback_data=f"decrease_{product_id}"),
                InlineKeyboardButton(text=str(current_quantity), callback_data="no_action"), 
                InlineKeyboardButton(text="+", callback_data=f"increase_{product_id}")
            ],
            [InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add_{product_id}")],
            [
                InlineKeyboardButton(text="Добавили? Оформляем заказ?", callback_data="checkout")
            ],
            [InlineKeyboardButton(text="... или продолжить покупки?", callback_data="continue_shopping")],
            [InlineKeyboardButton(text="Назад", callback_data=f"category_{product['category']}")]
        ])
        try:
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=f"<b>{product['name']}</b>\n\nЦена: {product['price']}₽",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    text=f"<b>{product['name']}</b>\n\nЦена: {product['price']}₽",
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения: {e}")

@dp.callback_query(F.data.startswith("increase_"))
async def increase_quantity(callback: types.CallbackQuery):
    """Увеличение количества товара"""
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[1])
    
    if user_id not in user_data:
        user_data[user_id] = {'main_message_id': None, 'other_messages': [], 'cart': {}}
    
    if 'cart' not in user_data[user_id]:
        user_data[user_id]['cart'] = {}
    
    # Увеличиваем количество на 1
    user_data[user_id]['cart'][product_id] = user_data[user_id]['cart'].get(product_id, 0) + 1
    
    # Обновляем сообщение
    await update_product_message(callback, product_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("decrease_"))
async def decrease_quantity(callback: types.CallbackQuery):
    """Уменьшение количества товара"""
    user_id = callback.from_user.id
    product_id = int(callback.data.split("_")[1])
    
    if user_id in user_data and 'cart' in user_data[user_id]:
        if product_id in user_data[user_id]['cart']:
            if user_data[user_id]['cart'][product_id] > 1:
                user_data[user_id]['cart'][product_id] -= 1
            else:
                del user_data[user_id]['cart'][product_id]
    
    # Обновляем сообщение
    await update_product_message(callback, product_id)
    await callback.answer()

async def update_product_message(callback: types.CallbackQuery, product_id: int):
    """Обновляет сообщение с товаром"""
    user_id = callback.from_user.id
    product = get_product(product_id)
    
    if not product:
        return
    
    current_quantity = user_data[user_id].get('cart', {}).get(product_id, 0)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="-", callback_data=f"decrease_{product_id}"),
            InlineKeyboardButton(text=str(current_quantity), callback_data="no_action"), 
            InlineKeyboardButton(text="+", callback_data=f"increase_{product_id}")
        ],
        [InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add_{product_id}")],
        [
            InlineKeyboardButton(text="Добавили? Оформляем заказ?", callback_data="checkout")
        ],
        [InlineKeyboardButton(text="... или продолжить покупки?", callback_data="continue_shopping")],
        [InlineKeyboardButton(text="Назад", callback_data=f"category_{product['category']}")]
    ])
    
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=f"<b>{product['name']}</b>\n\nЦена: {product['price']}₽",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                text=f"<b>{product['name']}</b>\n\nЦена: {product['price']}₽",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Ошибка при обновлении сообщения: {e}")

@dp.callback_query(F.data == "no_action")
async def no_action(callback: types.CallbackQuery):
    """Пустое действие при нажатии на количество"""
    await callback.answer()

@dp.callback_query(F.data == "checkout")
async def checkout(callback: types.CallbackQuery, state: FSMContext):
    """Оформление заказа с запросом номера телефона"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    if user_id not in user_data or 'cart' not in user_data[user_id] or not user_data[user_id]['cart']:
        await callback.answer("Ваша корзина пуста!")
        return
    
    # Формируем текст заказа
    order_text = "Ваш заказ:\n\n"
    total = 0
    for product_id, quantity in user_data[user_id]['cart'].items():
        product = get_product(product_id)
        if product:
            order_text += f"{product['name']} - {quantity} шт. x {product['price']}₽ = {quantity * product['price']}₽\n"
            total += quantity * product['price']
    
    order_text += f"\nИтого: {total}₽\n\n"
    order_text += "Пожалуйста, введите ваш номер телефона в формате +79991234567:"
    
    # Создаем клавиатуру только с кнопкой "Вернуться в главное меню"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Вернуться в главное меню")]
        ],
        resize_keyboard=True
    )
    
    await bot.send_message(
        chat_id,
        order_text,
        reply_markup=keyboard
    )
    
    # Устанавливаем состояние ожидания номера телефона
    await state.set_state(Form.waiting_for_phone_manual)
    await callback.answer()

@dp.message(Form.waiting_for_phone_manual)
async def process_manual_phone(message: types.Message, state: FSMContext):
    """Обработка номера, введенного вручную"""
    if message.text == "Вернуться в главное меню":
        await state.clear()
        await back_to_main_menu(message)
        return
    
    phone_number = message.text
    
    # Простая валидация номера
    if not phone_number.replace('+', '').isdigit() or len(phone_number.replace('+', '')) < 10:
        await message.reply("Пожалуйста, введите корректный номер телефона (например, +79991234567):")
        return
    
    # Сохраняем номер телефона
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['phone'] = phone_number
    
    # Запрашиваем адрес доставки
    await message.reply(
        "Спасибо! Теперь укажите, пожалуйста, адрес доставки:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Вернуться в главное меню")]
            ],
            resize_keyboard=True
        )
    )
    
    # Переходим в состояние ожидания адреса
    await state.set_state(Form.waiting_for_address)
async def save_phone_and_request_address(message: types.Message, phone_number: str, state: FSMContext):
    """Сохраняет номер и запрашивает адрес (общая функция)"""
    user_id = message.from_user.id
    
    # Сохраняем номер телефона
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['phone'] = phone_number
    
    # Запрашиваем адрес доставки
    await message.reply(
        "Спасибо! Теперь укажите, пожалуйста, адрес доставки:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Вернуться в главное меню")]
            ],
            resize_keyboard=True
        )
    )
    
    # Переходим в состояние ожидания адреса
    await state.set_state(Form.waiting_for_address)

@dp.message(Form.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    """Обработка введенного адреса"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if message.text == "Вернуться в главное меню":
        await state.clear()
        await back_to_main_menu(message)
        return
    
    address = message.text
    
    # Сохраняем адрес
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['address'] = address
    
    # Формируем финальное сообщение с заказом
    order_text = "Ваш заказ принят!\n\n"
    total = 0
    for product_id, quantity in user_data[user_id]['cart'].items():
        product = get_product(product_id)
        if product:
            order_text += f"{product['name']} - {quantity} шт. x {product['price']}₽ = {quantity * product['price']}₽\n"
            total += quantity * product['price']
    
    order_text += f"\nИтого: {total}₽\n\n"
    order_text += f"Номер телефона: {user_data[user_id].get('phone', 'не указан')}\n"
    order_text += f"Адрес доставки: {address}\n\n"
    order_text += "С вами свяжется оператор для подтверждения заказа."
    
    # Очищаем корзину после оформления
    user_data[user_id]['cart'] = {}
    
    await bot.send_message(
        chat_id,
        order_text,
        reply_markup=get_main_keyboard()
    )
    
    # Сбрасываем состояние
    await state.clear()
@dp.message(F.text == "Вернуться в главное меню")
async def back_to_main_menu(message: types.Message):
    """Обработчик возврата в главное меню"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await update_main_message(chat_id, user_id)
    await clean_other_messages(chat_id, user_id)
    await delete_user_message(message)

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    """Очистка корзины"""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    if user_id in user_data and 'cart' in user_data[user_id]:
        user_data[user_id]['cart'] = {}
    
    await callback.answer("Корзина очищена!")
    
    # Создаем временное сообщение для вызова show_cart
    fake_message = types.Message(
        message_id=0,
        date=0,
        chat=Chat(id=chat_id, type="private"),
        from_user=callback.from_user,
        text=""
    )
    await show_cart(fake_message)

async def main():
    initialize_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())