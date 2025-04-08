import sqlite3
from typing import Dict, Optional, List, Union

def create_tables():
    """Создает таблицы в базе данных"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        image_url TEXT,
        category_id TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_category(category_id: str, name: str) -> bool:
    """Добавляет категорию в базу данных"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO categories (category_id, name) VALUES (?, ?)', (category_id, name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Категория уже существует
        return False
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении категории: {e}")
        return False
    finally:
        conn.close()

def add_product(name: str, price: int, image_url: Optional[str], category_id: str) -> bool:
    """Добавляет товар в базу данных"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO products (name, price, image_url, category_id) VALUES (?, ?, ?, ?)',
            (name, price, image_url, category_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении товара: {e}")
        return False
    finally:
        conn.close()

def get_categories() -> Dict[str, str]:
    """Возвращает словарь категорий {category_id: name}"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT category_id, name FROM categories')
        return {row[0]: row[1] for row in cursor.fetchall()}
    except sqlite3.Error as e:
        print(f"Ошибка при получении категорий: {e}")
        return {}
    finally:
        conn.close()

def get_all_categories() -> List[Dict]:
    """Возвращает список всех категорий с полной информацией"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, category_id, name FROM categories')
        return [
            {'id': row[0], 'category_id': row[1], 'name': row[2]}
            for row in cursor.fetchall()
        ]
    except sqlite3.Error as e:
        print(f"Ошибка при получении категорий: {e}")
        return []
    finally:
        conn.close()

def get_products_by_category(category_id: str) -> Dict[int, Dict]:
    """Возвращает товары в категории, отсортированные по цене (от дешевых к дорогим)"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT id, name, price, image_url FROM products WHERE category_id = ? ORDER BY price ASC',
            (category_id,)
        )
        return {
            row[0]: {
                'name': row[1],
                'price': row[2],
                'image_url': row[3],
                'category': category_id
            }
            for row in cursor.fetchall()
        }
    except sqlite3.Error as e:
        print(f"Ошибка при получении товаров: {e}")
        return {}
    finally:
        conn.close()

def get_all_products() -> List[Dict]:
    """Возвращает список всех товаров с информацией о категориях"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT p.id, p.name, p.price, p.image_url, p.category_id, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
        ''')
        return [
            {
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'image_url': row[3],
                'category': row[4],
                'category_name': row[5]
            }
            for row in cursor.fetchall()
        ]
    except sqlite3.Error as e:
        print(f"Ошибка при получении товаров: {e}")
        return []
    finally:
        conn.close()

def get_product(product_id: int) -> Optional[Dict]:
    """Возвращает информацию о товаре"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''SELECT p.id, p.name, p.price, p.image_url, p.category_id, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.id = ?''',
            (product_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'image_url': row[3],
                'category': row[4],
                'category_name': row[5]
            }
        return None
    except sqlite3.Error as e:
        print(f"Ошибка при получении товара: {e}")
        return None
    finally:
        conn.close()

def update_category(category_id: str, new_name: str) -> bool:
    """Обновляет название категории"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE categories SET name = ? WHERE category_id = ?',
            (new_name, category_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении категории: {e}")
        return False
    finally:
        conn.close()

def delete_category(category_id: str) -> bool:
    """Удаляет категорию (и все связанные товары)"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM products WHERE category_id = ?', (category_id,))
        cursor.execute('DELETE FROM categories WHERE category_id = ?', (category_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при удалении категории: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_product(product_id: int) -> bool:
    """Удаляет товар"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Ошибка при удалении товара: {e}")
        return False
    finally:
        conn.close()

def initialize_database():
    """Инициализирует базу данных с тестовыми данными"""
    print("Инициализация базы данных...")
    create_tables()
    
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) FROM categories')
        if cursor.fetchone()[0] == 0:
            print("Добавление тестовых данных...")
            
            categories = [
                ("STICKS", "Стики"),
                ("BEER", "Пиво"),
                ("CIGARETTES", "Сигареты"),
                ("WINE", "Вино"),
                ("WHISKEY", "Виски"),
                ("VODKA", "Водка"),
                ("COGNAC", "Коньяк"),
                ("CHAMPAGNE", "Игристое и шампанское"),
                ("SNACKS", "Снеки"),
                ("HQD", "Hqd")
            ]
            
            cursor.executemany(
                'INSERT OR IGNORE INTO categories (category_id, name) VALUES (?, ?)',
                categories
            )
            
            products = [
                ("Fiit Viola", 270, "Fiit_Viola.jpg", "STICKS"),
                ("Corona Extra 0,35 л", 195, "Corona_extra.jpg", "BEER"),
                ("Parliament Aqua Blue", 435, "Parliament.jpg", "CIGARETTES"),
                ("Duffour Gascogne красное сухое 0,75 л.", 1500, "Duffour.jpg", "WINE"),
                ("Jameson 0,7 л", 2300, "Jameson.jpg", "WHISKEY"),
                ("Beluga Transatlantic 0,7 л", 2200, "Beluga.jpg", "VODKA"),
                ("Ной Традиционный 5 лет 0,5 л", 1300, "Noi.jpg", "COGNAC"),
                ("игристое Martini Prosecco белое сухое 0,75 л", 1550, "Martini.jpg", "CHAMPAGNE"),
                ("Картофельные чипсы Lay's Сметана и лук 140 г", 230, "Lays.jpg", "SNACKS"),
                ("HQD NEO PRO 18000 Triple Berry (Тройная Ягода)", 1620, "HQD.jpg", "HQD")
            ]
            
            cursor.executemany(
                'INSERT INTO products (name, price, image_url, category_id) VALUES (?, ?, ?, ?)',
                products
            )
            
            conn.commit()
            print("Тестовые данные успешно добавлены")
        else:
            print("База данных уже содержит данные, пропускаем инициализацию")
    except sqlite3.Error as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_product(
    product_id: int,
    name: Optional[str] = None,
    price: Optional[int] = None,
    image_url: Optional[str] = None,
    category_id: Optional[str] = None
) -> bool:
    """Обновляет информацию о товаре"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    try:
        # Получаем текущие данные товара
        current_data = get_product(product_id)
        if not current_data:
            return False

        # Подготавливаем новые значения
        new_name = name if name is not None else current_data['name']
        new_price = price if price is not None else current_data['price']
        new_image_url = image_url if image_url is not None else current_data['image_url']
        new_category_id = category_id if category_id is not None else current_data['category']

        cursor.execute(
            '''UPDATE products 
            SET name = ?, price = ?, image_url = ?, category_id = ?
            WHERE id = ?''',
            (new_name, new_price, new_image_url, new_category_id, product_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении товара: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
