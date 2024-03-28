import psycopg2
from psycopg2 import sql
import os
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

# Создаем глобальное соединение и курсор
conn = psycopg2.connect(
    dbname="DBforWebApp",
    user="postgres",
    password="cpokyxa11111",
    host="127.0.0.1",
    port="5432"
)

cursor = conn.cursor()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def create_user(username, password):
    """Создание нового пользователя."""
    try:
        query = sql.SQL('INSERT INTO users (username, password) VALUES (%s, %s);')
        with conn.cursor() as cursor:
            cursor.execute(query, (username, password))
            conn.commit()
    except Exception as e:
        conn.rollback()  # Откатываем транзакцию
        print(f"Ошибка при выполнении SQL-запроса: {e}")

def get_user_by_username(username):
    """Получение пользователя по имени пользователя."""
    try:
        query = sql.SQL('SELECT * FROM users WHERE username = %s;')
        with conn.cursor() as cursor:
            cursor.execute(query, (username,))
            return cursor.fetchone()
    except Exception as e:
        conn.rollback()  # Откатываем транзакцию
        print(f"Ошибка при выполнении SQL-запроса: {e}")

def create_post(title, content, image_url):
    """Создание нового поста."""
    try:
        cursor = conn.cursor()

        # Вставляем данные о посте в таблицу
        query = sql.SQL("""
            INSERT INTO post (title, content, image_url) 
            VALUES (%s, %s, %s)
        """)
        cursor.execute(query, (title, content, image_url))
        conn.commit()
    except Exception as e:
        conn.rollback()  # Откатываем транзакцию
        print(f"Ошибка при создании поста: {e}")
    finally:
        if cursor:
            cursor.close()

def get_all_posts():
    """Получение списка всех постов."""
    try:
        cursor = conn.cursor()

        # Выбираем все посты из таблицы
        query = sql.SQL("SELECT * FROM post ORDER BY created_at DESC")
        cursor.execute(query)

        # Возвращаем список постов
        return cursor.fetchall()
    except Exception as e:
        conn.rollback()  # Откатываем транзакцию
        print(f"Ошибка при получении постов: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image):
    """Сохранение изображения и возврат его URL."""
    try:
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(file_path)

            # Возвращаем URL сохраненного изображения
            return file_path
        else:
            return None
    except Exception as e:
        print(f"Ошибка при сохранении изображения: {e}")
        return None

def delete_post_by_id(post_id):
    """Удаление поста по его ID."""
    try:
        cursor = conn.cursor()
        query = sql.SQL("DELETE FROM post WHERE id = %s;")
        cursor.execute(query, (post_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении поста: {e}")
    finally:
        if cursor:
            cursor.close()

def create_admin_user():
    try:
        query = sql.SQL("""
            INSERT INTO users (username, password)
            VALUES (%s, %s)
            ON CONFLICT (username) DO NOTHING;
        """)
        cursor.execute(query, ('Brovkin', generate_password_hash('cpokyxa11111', method='pbkdf2:sha256')))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании администратора: {e}")
    finally:
        if cursor:
            cursor.close()

def create_comment(post_id, user_id, content):
    """Создание нового комментария."""
    try:
        query = sql.SQL("""
            INSERT INTO comments (post_id, user_id, content) 
            VALUES (%s, %s, %s)
        """)
        with conn.cursor() as cursor:
            cursor.execute(query, (post_id, user_id, content))
            conn.commit()
    except Exception as e:
        conn.rollback()  # Откатываем транзакцию
        print(f"Ошибка при создании комментария: {e}")

def get_comments_by_post_id(post_id):
    """Получение комментариев по ID поста."""
    try:
        query = sql.SQL("SELECT * FROM comments WHERE post_id = %s ORDER BY created_at ASC")
        with conn.cursor() as cursor:
            cursor.execute(query, (post_id,))
            return cursor.fetchall()
    except Exception as e:
        conn.rollback()  # Откатываем транзакцию
        print(f"Ошибка при получении комментариев: {e}")

# Для правильного закрытия соединения с базой данных
def close_connection():
    cursor.close()
    conn.close()