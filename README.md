# 🛍️ Telegram Shop Bot

## 📝 Описание проекта

Telegram Shop Bot - это полнофункциональный бот для интернет-магазина с возможностью:
- 📂 Просмотра каталога товаров по категориям
- 🛒 Добавления товаров в корзину
- 📦 Оформления заказов
- 📞 Связи с оператором
- 👨‍💻 Админ-панелью для управления товарами и категориями

Бот использует современные технологии для удобства пользователей и администраторов магазина.

## 🌟 Особенности

### Для покупателей:
- 🖼️ Просмотр товаров с фотографиями
- 🔍 Удобная навигация по категориям
- ➕➖ Изменение количества товаров в корзине
- 📱 Удобный ввод контактных данных
- 📊 Автоматический расчет суммы заказа

### Для администраторов:
- 📁 Полное управление каталогом товаров
- ✏️ Редактирование названий, цен, категорий
- 🖼️ Загрузка изображений товаров
- 📊 Экспорт заказов в Google Таблицы
- 🔒 Защищенный доступ к админ-панели

## 🛠 Технологии

- **Python 3.10+**
- **aiogram 3.x** - современная библиотека для Telegram ботов
- **SQLite** - база данных для хранения товаров и категорий
- **Google Sheets API** - экспорт заказов
- **Gspread** - работа с Google Таблицами
- **Logging** - логирование действий

## ⚙️ Установка и настройка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/telegram-shop-bot.git
   cd telegram-shop-bot
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Создайте файл `config.py` на основе примера:
   ```python
   BOT_TOKEN = "ваш_токен_бота"
   ADMIN_ID = ["ваш_telegram_id"]  # Можно несколько через запятую
   IMAGE_FOLDER = "images"  # Папка для хранения изображений товаров
   
   # Настройки Google Sheets (опционально)
   GOOGLE_SHEETS_CREDENTIALS_FILE = "credentials.json"
   GOOGLE_SHEET_NAME = "Название вашей таблицы"
   GOOGLE_SHEET_WORKSHEET = "Название листа"
   ```

4. Запустите бота:
   ```bash
   python main.py
   ```

## 📂 Структура проекта

```
telegram-shop-bot/
├── main.py            # Основной код бота
├── database.py        # Работа с базой данных
├── admin.py           # Админ-панель
├── config.py          # Конфигурационные параметры
├── images/            # Папка для изображений товаров
├── shop.db            # База данных SQLite (создается автоматически)
└── README.md          # Этот файл
```

## 📌 Использование

### Команды для пользователей:
- `/start` - начать работу с ботом
- `Каталог` - просмотр категорий товаров
- `Корзина` - просмотр и редактирование корзины
- `Доставка` - информация о доставке
- `Онлайн-чат` - связь с оператором
- `Позвонить` - номер телефона магазина

### Админ-команды:
- `/admin` - вход в админ-панель
- Управление категориями:
  - Добавление/удаление категорий
  - Редактирование названий
- Управление товарами:
  - Добавление/удаление товаров
  - Редактирование названий, цен, изображений
  - Изменение категорий товаров
