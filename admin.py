from aiogram import Bot, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (
    get_all_categories,
    get_all_products,
    add_category,
    add_product,
    update_category,
    update_product,
    delete_category,
    delete_product,
    get_products_by_category,
    get_product
)
from config import ADMIN_ID, IMAGE_FOLDER
import os
import shutil
import logging
from math import ceil

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы для пагинации
ITEMS_PER_PAGE = 5  # Количество элементов на странице

# Создаем папку для изображений, если ее нет
os.makedirs(IMAGE_FOLDER, exist_ok=True)

class AdminStates(StatesGroup):
    waiting_for_category_id = State()
    waiting_for_category_name = State()
    waiting_for_product_name = State()
    waiting_for_product_price = State()
    waiting_for_product_image = State()
    waiting_for_new_category_name = State()
    waiting_for_edit_product_name = State()
    waiting_for_edit_product_price = State()
    waiting_for_edit_product_image = State()
    waiting_for_edit_product_category = State()

async def setup_admin_handlers(dp):
    """Настройка обработчиков для админ-панели"""
    
    def is_admin(user_id: int):
        return str(user_id) in ADMIN_ID
    
    async def save_photo(bot: Bot, file_id: str, filename: str) -> str:
        """Сохраняет фото на сервере и возвращает имя файла"""
        file = await bot.get_file(file_id)
        ext = file.file_path.split('.')[-1]
        save_path = os.path.join(IMAGE_FOLDER, f"{filename}.{ext}")
        
        if os.path.exists(save_path):
            os.remove(save_path)
        
        await bot.download_file(file.file_path, save_path)
        return f"{filename}.{ext}"

    def get_admin_keyboard():
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Управление категориями"))
        builder.row(KeyboardButton(text="Управление товарами"))
        builder.row(KeyboardButton(text="Выйти из админ-панели"))
        return builder.as_markup(resize_keyboard=True)
    
    def get_categories_admin_keyboard():
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Добавить категорию",
            callback_data="admin_add_category"
        ))
        builder.add(InlineKeyboardButton(
            text="Список категорий",
            callback_data="admin_list_categories_page_0"
        ))
        builder.adjust(1)
        return builder.as_markup()
    
    def get_products_admin_keyboard():
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Добавить товар",
            callback_data="admin_add_product"
        ))
        builder.add(InlineKeyboardButton(
            text="Список товаров",
            callback_data="admin_list_products_page_0"
        ))
        builder.adjust(1)
        return builder.as_markup()
    
    def get_category_actions_keyboard(category_id: str, page: int = 0):
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Изменить название",
            callback_data=f"admin_edit_category_{category_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="Удалить категорию",
            callback_data=f"admin_delete_category_{category_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="Назад к списку",
            callback_data=f"admin_list_categories_page_{page}"
        ))
        builder.adjust(1)
        return builder.as_markup()
    
    def get_product_actions_keyboard(product_id: int, page: int = 0):
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Изменить товар",
            callback_data=f"admin_edit_product_{product_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="Удалить товар",
            callback_data=f"admin_delete_product_{product_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="Назад к списку",
            callback_data=f"admin_list_products_page_{page}"
        ))
        builder.adjust(1)
        return builder.as_markup()
    
    def get_back_to_admin_keyboard():
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Вернуться в админ-панель",
            callback_data="admin_back_to_main"
        ))
        return builder.as_markup()

    def build_pagination_keyboard(page: int, total_pages: int, prefix: str):
        builder = InlineKeyboardBuilder()
        
        # Горизонтальная пагинация
        if page > 0:
            builder.add(InlineKeyboardButton(
                text="⬅ Назад",
                callback_data=f"{prefix}{page - 1}"
            ))
        
        builder.add(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="no_action"
        ))
        
        if page < total_pages - 1:
            builder.add(InlineKeyboardButton(
                text="Вперед ➡",
                callback_data=f"{prefix}{page + 1}"
            ))
        
        # Все кнопки пагинации в один ряд
        builder.adjust(3)
        
        return builder

    @dp.message(Command("admin"))
    async def cmd_admin(message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("У вас нет прав доступа к этой команде.")
            return
        
        await message.answer(
            "Админ-панель:",
            reply_markup=get_admin_keyboard()
        )
    
    @dp.message(F.text == "Выйти из админ-панели")
    async def admin_exit(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        
        await message.answer(
            "Вы вышли из админ-панели.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    
    @dp.message(F.text == "Управление категориями")
    async def admin_categories(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        
        await message.answer(
            "Управление категориями:",
            reply_markup=get_categories_admin_keyboard()
        )
    
    @dp.message(F.text == "Управление товарами")
    async def admin_products(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        
        await message.answer(
            "Управление товарами:",
            reply_markup=get_products_admin_keyboard()
        )
    
    @dp.callback_query(F.data == "admin_add_category")
    async def admin_add_category_callback(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            return
        
        await callback.message.answer(
            "Введите ID новой категории (латинскими буквами, без пробелов):"
        )
        await state.set_state(AdminStates.waiting_for_category_id)
        await callback.answer()
    
    @dp.message(AdminStates.waiting_for_category_id)
    async def admin_process_category_id(message: types.Message, state: FSMContext):
        category_id = message.text.strip()
        await state.update_data(category_id=category_id)
        await message.answer("Введите название категории:")
        await state.set_state(AdminStates.waiting_for_category_name)
    
    @dp.message(AdminStates.waiting_for_category_name)
    async def admin_process_category_name(message: types.Message, state: FSMContext):
        category_name = message.text.strip()
        data = await state.get_data()
        category_id = data.get("category_id")
        
        if add_category(category_id, category_name):
            await message.answer(
                f"Категория '{category_name}' успешно добавлена!",
                reply_markup=get_back_to_admin_keyboard()
            )
        else:
            await message.answer(
                "Ошибка при добавлении категории",
                reply_markup=get_back_to_admin_keyboard()
            )
        
        await state.clear()
    
    @dp.callback_query(F.data.startswith("admin_list_categories_page_"))
    async def admin_list_categories_callback(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            return
        
        try:
            page = int(callback.data.split("_")[-1])
        except:
            page = 0
        
        categories = get_all_categories()
        if not categories:
            await callback.message.answer(
                "Нет доступных категорий",
                reply_markup=get_back_to_admin_keyboard()
            )
            return
        
        total_pages = ceil(len(categories) / ITEMS_PER_PAGE)
        if page >= total_pages:
            page = total_pages - 1
        
        start_idx = page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_categories = categories[start_idx:end_idx]
        
        text = f"Список категорий (Страница {page + 1}/{total_pages}):\n\n"
        for category in current_categories:
            text += f"{category['name']} (ID: {category['category_id']})\n"
        
        # Создаем клавиатуру с пагинацией
        pagination_builder = build_pagination_keyboard(
            page, total_pages, "admin_list_categories_page_"
        )
        
        # Создаем клавиатуру с категориями
        categories_builder = InlineKeyboardBuilder()
        for category in current_categories:
            categories_builder.add(InlineKeyboardButton(
                text=category['name'],
                callback_data=f"admin_category_{category['category_id']}_{page}"
            ))
        categories_builder.adjust(2)
        
        # Объединяем обе клавиатуры
        pagination_builder.attach(categories_builder)
        
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=pagination_builder.as_markup()
            )
        except:
            await callback.message.answer(
                text=text,
                reply_markup=pagination_builder.as_markup()
            )
        
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_category_"))
    async def admin_category_actions(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            return
        
        parts = callback.data.split("_")
        category_id = parts[2]
        page = int(parts[3]) if len(parts) > 3 else 0
        
        categories = get_all_categories()
        category = next((c for c in categories if c['category_id'] == category_id), None)
        
        if not category:
            await callback.answer("Категория не найдена")
            return
        
        await callback.message.answer(
            f"Категория: {category['name']}\nID: {category['category_id']}",
            reply_markup=get_category_actions_keyboard(category_id, page)
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_edit_category_"))
    async def admin_edit_category(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            return
        
        category_id = callback.data.split("_")[3]
        await state.update_data(category_id=category_id)
        await callback.message.answer("Введите новое название категории:")
        await state.set_state(AdminStates.waiting_for_new_category_name)
        await callback.answer()
    
    @dp.message(AdminStates.waiting_for_new_category_name)
    async def admin_process_new_category_name(message: types.Message, state: FSMContext):
        new_name = message.text.strip()
        data = await state.get_data()
        category_id = data.get("category_id")
        
        if update_category(category_id, new_name):
            await message.answer(
                f"Название категории успешно изменено на '{new_name}'!",
                reply_markup=get_back_to_admin_keyboard()
            )
        else:
            await message.answer(
                "Ошибка при изменении категории",
                reply_markup=get_back_to_admin_keyboard()
            )
        
        await state.clear()
    
    @dp.callback_query(F.data.startswith("admin_delete_category_"))
    async def admin_delete_category(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            return
        
        category_id = callback.data.split("_")[3]
        categories = get_all_categories()
        category = next((c for c in categories if c['category_id'] == category_id), None)
        
        if not category:
            await callback.answer("Категория не найдена")
            return
        
        if delete_category(category_id):
            await callback.message.answer(
                f"Категория '{category['name']}' успешно удалена!",
                reply_markup=get_back_to_admin_keyboard()
            )
        else:
            await callback.message.answer(
                "Ошибка при удалении категории",
                reply_markup=get_back_to_admin_keyboard()
            )
        await callback.answer()
    
    @dp.callback_query(F.data == "admin_add_product")
    async def admin_add_product_callback(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            return
        
        categories = get_all_categories()
        if not categories:
            await callback.message.answer(
                "Сначала создайте хотя бы одну категорию",
                reply_markup=get_back_to_admin_keyboard()
            )
            return
        
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.add(InlineKeyboardButton(
                text=category['name'],
                callback_data=f"admin_add_product_to_{category['category_id']}"
            ))
        builder.adjust(2)
        
        await callback.message.answer(
            "Выберите категорию для нового товара:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_add_product_to_"))
    async def admin_select_category_for_product(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            return
        
        category_id = callback.data.split("_")[4]
        await state.update_data(category_id=category_id)
        await callback.message.answer("Введите название товара:")
        await state.set_state(AdminStates.waiting_for_product_name)
        await callback.answer()
    
    @dp.message(AdminStates.waiting_for_product_name)
    async def admin_process_product_name(message: types.Message, state: FSMContext):
        product_name = message.text.strip()
        await state.update_data(product_name=product_name)
        await message.answer("Введите цену товара (только число):")
        await state.set_state(AdminStates.waiting_for_product_price)
    
    @dp.message(AdminStates.waiting_for_product_price)
    async def admin_process_product_price(message: types.Message, state: FSMContext):
        try:
            price = int(message.text.strip())
            await state.update_data(price=price)
            await message.answer("Отправьте фото товара (или отправьте 'нет' чтобы пропустить):")
            await state.set_state(AdminStates.waiting_for_product_image)
        except ValueError:
            await message.answer("Пожалуйста, введите корректную цену (только число):")
    
    @dp.message(AdminStates.waiting_for_product_image)
    async def admin_process_product_image(message: types.Message, state: FSMContext):
        data = await state.get_data()
        product_name = data.get("product_name")
        price = data.get("price")
        category_id = data.get("category_id")
        image_filename = None
        
        if message.text and message.text.lower() == "нет":
            image_filename = ""
        elif message.photo:
            try:
                filename_base = "".join(c for c in product_name if c.isalnum())
                image_filename = await save_photo(message.bot, message.photo[-1].file_id, filename_base)
            except Exception as e:
                await message.answer(f"Ошибка при сохранении изображения: {e}")
                return
        else:
            await message.answer("Пожалуйста, отправьте фото или 'нет'")
            return
        
        if add_product(product_name, price, image_filename, category_id):
            await message.answer(
                f"Товар '{product_name}' успешно добавлен!",
                reply_markup=get_back_to_admin_keyboard()
            )
        else:
            await message.answer(
                "Ошибка при добавлении товара",
                reply_markup=get_back_to_admin_keyboard()
            )
        
        await state.clear()
    

    @dp.callback_query(F.data.startswith("admin_list_products_page_"))
    async def admin_list_products_callback(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            return
        
        try:
            page = int(callback.data.split("_")[-1])
        except:
            page = 0
        
        products = get_all_products()
        if not products:
            await callback.message.answer(
                "Нет доступных товаров",
                reply_markup=get_back_to_admin_keyboard()
            )
            return
        
        total_pages = ceil(len(products) / ITEMS_PER_PAGE)
        if page >= total_pages:
            page = total_pages - 1
        
        start_idx = page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_products = products[start_idx:end_idx]
        
        text = "Список товаров:\n\n"
        for product in current_products:
            text += f"• {product['name']} - {product['price']}Р (ID: {product['id']})\n"
        
        # Создаем клавиатуру с пагинацией (горизонтально)
        pagination_builder = build_pagination_keyboard(
            page, total_pages, "admin_list_products_page_"
        )
        
        # Создаем клавиатуру с товарами (горизонтально)
        products_builder = InlineKeyboardBuilder()
        for product in current_products:
            products_builder.add(InlineKeyboardButton(
                text=f"{product['name']}",
                callback_data=f"admin_product_{product['id']}_{page}"
            ))
        
        # 5 товара в ряд
        products_builder.adjust(5)
        
        # Объединяем обе клавиатуры
        pagination_builder.attach(products_builder)
        
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=pagination_builder.as_markup()
            )
        except:
            await callback.message.answer(
                text=text,
                reply_markup=pagination_builder.as_markup()
            )
        
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_product_"))
    async def admin_product_actions(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            return
        
        parts = callback.data.split("_")
        product_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0
        
        product = get_product(product_id)
        
        if not product:
            await callback.answer("Товар не найден")
            return
        
        # Показываем изображение товара, если оно есть
        image_path = os.path.join(IMAGE_FOLDER, product['image_url']) if product.get('image_url') else None
        
        if image_path and os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await callback.message.delete()
            sent_message = await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=photo,
                caption=f"Товар: {product['name']}\nЦена: {product['price']}Р\nID: {product_id}",
                reply_markup=get_product_actions_keyboard(product_id, page)
            )
        else:
            await callback.message.edit_text(
                f"Товар: {product['name']}\nЦена: {product['price']}Р\nID: {product_id}",
                reply_markup=get_product_actions_keyboard(product_id, page)
            )
        
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_edit_product_"))
    async def admin_edit_product(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            return
        
        product_id = int(callback.data.split("_")[3])
        product = get_product(product_id)
        
        if not product:
            await callback.answer("Товар не найден")
            return
        
        await state.update_data(product_id=product_id)
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Изменить название",
            callback_data="edit_product_name"
        ))
        builder.add(InlineKeyboardButton(
            text="Изменить цену",
            callback_data="edit_product_price"
        ))
        builder.add(InlineKeyboardButton(
            text="Изменить изображение",
            callback_data="edit_product_image"
        ))
        builder.add(InlineKeyboardButton(
            text="Изменить категорию",
            callback_data="edit_product_category"
        ))
        builder.add(InlineKeyboardButton(
            text="Назад",
            callback_data=f"admin_product_{product_id}"
        ))
        builder.adjust(1)
        
        await callback.message.answer(
            "Что вы хотите изменить?",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "edit_product_name")
    async def edit_product_name_handler(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer("Введите новое название товара:")
        await state.set_state(AdminStates.waiting_for_edit_product_name)
        await callback.answer()
    
    @dp.message(AdminStates.waiting_for_edit_product_name)
    async def process_edit_product_name(message: types.Message, state: FSMContext):
        data = await state.get_data()
        product_id = data.get("product_id")
        
        if update_product(product_id, name=message.text):
            await message.answer("Название товара успешно изменено!", reply_markup=get_back_to_admin_keyboard())
        else:
            await message.answer("Ошибка при изменении названия", reply_markup=get_back_to_admin_keyboard())
        
        await state.clear()
    
    @dp.callback_query(F.data == "edit_product_price")
    async def edit_product_price_handler(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer("Введите новую цену товара:")
        await state.set_state(AdminStates.waiting_for_edit_product_price)
        await callback.answer()
    
    @dp.message(AdminStates.waiting_for_edit_product_price)
    async def process_edit_product_price(message: types.Message, state: FSMContext):
        try:
            new_price = int(message.text)
            data = await state.get_data()
            product_id = data.get("product_id")
            
            if update_product(product_id, price=new_price):
                await message.answer("Цена товара успешно изменена!", reply_markup=get_back_to_admin_keyboard())
            else:
                await message.answer("Ошибка при изменении цены", reply_markup=get_back_to_admin_keyboard())
        except ValueError:
            await message.answer("Пожалуйста, введите корректную цену (целое число)")
            return
        
        await state.clear()
    
    @dp.callback_query(F.data == "edit_product_image")
    async def edit_product_image_handler(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.answer("Отправьте новое изображение товара или 'нет' для удаления текущего:")
        await state.set_state(AdminStates.waiting_for_edit_product_image)
        await callback.answer()
    
    @dp.message(AdminStates.waiting_for_edit_product_image, F.photo | F.text)
    async def process_edit_product_image(message: types.Message, state: FSMContext):
        data = await state.get_data()
        product_id = data.get("product_id")
        product = get_product(product_id)
        
        if not product:
            await message.answer("Товар не найден")
            await state.clear()
            return
        
        new_image = None
        
        if message.text and message.text.lower() == "нет":
            # Удаляем старое изображение
            if product.get('image_url'):
                old_image_path = os.path.join(IMAGE_FOLDER, product['image_url'])
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            new_image = ""
        elif message.photo:
            try:
                filename_base = f"product_{product_id}"
                new_image = await save_photo(message.bot, message.photo[-1].file_id, filename_base)
                
                # Удаляем старое изображение
                if product.get('image_url'):
                    old_image_path = os.path.join(IMAGE_FOLDER, product['image_url'])
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
            except Exception as e:
                await message.answer(f"Ошибка при сохранении изображения: {e}")
                return
        else:
            await message.answer("Пожалуйста, отправьте фото или 'нет'")
            return
        
        if update_product(product_id, image_url=new_image):
            await message.answer("Изображение товара успешно изменено!", reply_markup=get_back_to_admin_keyboard())
        else:
            await message.answer("Ошибка при изменении изображения", reply_markup=get_back_to_admin_keyboard())
        
        await state.clear()
    
    @dp.callback_query(F.data == "edit_product_category")
    async def edit_product_category_handler(callback: types.CallbackQuery, state: FSMContext):
        categories = get_all_categories()
        if not categories:
            await callback.answer("Нет доступных категорий")
            return
        
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.add(InlineKeyboardButton(
                text=category['name'],
                callback_data=f"set_product_category_{category['category_id']}"
            ))
        builder.adjust(2)
        
        await callback.message.answer(
            "Выберите новую категорию:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(AdminStates.waiting_for_edit_product_category)
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("set_product_category_"), AdminStates.waiting_for_edit_product_category)
    async def set_product_category_handler(callback: types.CallbackQuery, state: FSMContext):
        new_category_id = callback.data.split("_")[3]
        data = await state.get_data()
        product_id = data.get("product_id")
        
        if update_product(product_id, category_id=new_category_id):
            await callback.message.answer("Категория товара успешно изменена!", reply_markup=get_back_to_admin_keyboard())
        else:
            await callback.message.answer("Ошибка при изменении категории", reply_markup=get_back_to_admin_keyboard())
        
        await state.clear()
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_delete_product_"))
    async def admin_delete_product(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            return
        
        product_id = int(callback.data.split("_")[3])
        product = get_product(product_id)
        
        if not product:
            await callback.answer("Товар не найден")
            return
        
        if product.get('image_url'):
            image_path = os.path.join(IMAGE_FOLDER, product['image_url'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        if delete_product(product_id):
            await callback.message.answer(
                f"Товар '{product['name']}' успешно удален!",
                reply_markup=get_back_to_admin_keyboard()
            )
        else:
            await callback.message.answer(
                "Ошибка при удалении товара",
                reply_markup=get_back_to_admin_keyboard()
            )
        await callback.answer()
    
    @dp.callback_query(F.data == "admin_back_to_main")
    async def admin_back_to_main(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            return
        
        await callback.message.answer(
            "Админ-панель:",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "no_action")
    async def no_action_handler(callback: types.CallbackQuery):
        await callback.answer()
