from flask import Flask, render_template, redirect, request, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from bd import * # Импортируйте ваш модуль для работы с базой данных
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'WebAppBrovkin'
POSTS_PER_PAGE = 4  # Количество постов на одной странице

@app.route('/')
def index():
    if 'user_id' in session:
        username = session.get('username', '')  # Получаем значение 'username' из сессии, или пустую строку, если его нет
        return render_template('main.html', username=username)
    else:
        return render_template('main.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Проверка, существует ли пользователь с таким именем
        existing_user = get_user_by_username(username)
        if existing_user:
            flash('Пользователь с таким именем уже существует.', 'danger')
            return redirect(url_for('register'))

        # Хеширование пароля перед сохранением в базе данных
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Создание нового пользователя
        create_user(username, hashed_password)

        flash('Регистрация прошла успешно. Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)

        if user and check_password_hash(user[2], password):
            # Успешная аутентификация
            session['user_id'] = user[0]
            session['username'] = user[1]  # Устанавливаем username в сессии
            return redirect(url_for('admin_panel') if username == 'Brovkin' else 'user_panel')
        else:
            flash('Неправильное имя пользователя или пароль.', 'danger')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'user_id' in session:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            image_url = request.form['image_url']

            create_post(title, content, image_url)

        posts = get_all_posts()
        page = int(request.args.get('page', 1))
        start = (page - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        paginated_posts = posts[start:end]

        # Получаем комментарии для каждого поста
        post_comments = {post[0]: get_comments_by_post_id(post[0]) for post in paginated_posts}

        return render_template(
            'admin.html',
            username=session['username'],
            posts=paginated_posts,
            page=page,
            pages=range(1, len(posts) // POSTS_PER_PAGE + 2),
            post_comments=post_comments  # Передаем комментарии в шаблон
        )
    else:
        return redirect(url_for('index'))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    """Удаление комментария."""
    if 'user_id' in session:
        # Удаляем комментарий из базы данных по его ID
        delete_comment_by_id(comment_id)
        flash('Комментарий успешно удален.', 'success')
        return redirect(url_for('admin_panel'))
    else:
        return redirect(url_for('index'))

def delete_comment_by_id(comment_id):
    """Удаление комментария по его ID."""
    try:
        cursor = conn.cursor()
        query = sql.SQL("DELETE FROM comments WHERE id = %s;")
        cursor.execute(query, (comment_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении комментария: {e}")
    finally:
        if cursor:
            cursor.close()

@app.route('/user_panel')
def user_panel():
    if 'user_id' in session:
        username = session.get('username', '')

        # Get a list of all posts from the database
        posts = get_all_posts()

        # Get the current page number from the request, default to 1 if not specified
        page = int(request.args.get('page', 1))

        # Call the new function to get comments for each post
        post_comments = {post[0]: get_comments_by_post_id(post[0]) for post in posts}

        return render_template('user_panel.html', username=username, posts=posts, page=page, post_comments=post_comments)
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' in session:
        # Удаляем пост из базы данных по его ID
        delete_post_by_id(post_id)
        flash('Пост успешно удален.', 'success')
        return redirect(url_for('admin_panel'))
    else:
        return redirect(url_for('index'))

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' in session:
        user_id = session['user_id']
        content = request.form['comment']

        # Создаем новый комментарий
        create_comment(post_id, user_id, content)

        flash('Комментарий успешно добавлен.', 'success')
        return redirect(url_for('user_panel'))
    else:
        return redirect(url_for('index'))

@app.template_filter('to_local_datetime')
def to_local_datetime(value):
    if value:
        dt = datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S.%f')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return ''

@app.route('/contact', methods=['POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Отправляем сообщение на почтовый адрес
        send_email(name, email, message)

        flash('Сообщение успешно отправлено!', 'success')
        return redirect(url_for('index'))

    return render_template('index.html')

def send_email(name, email, message):
    # Укажите свои учетные данные для почтового ящика
    email_address = 'artembro2014@mail.ru'
    email_password = 'Pigedove12345'

    # Укажите почтовый адрес назначения
    to_email = 'artembro2014@mail.ru'

    # Создаем объект MIMEMultipart
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = to_email
    msg['Subject'] = 'Новое сообщение от пользователя: {}'.format(name)

    # Добавляем текст сообщения
    msg.attach(MIMEText(message, 'plain'))

    # Подключаемся к SMTP-серверу и отправляем сообщение
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(email_address, email_password)
        server.sendmail(email_address, to_email, msg.as_string())

if __name__ == '__main__':
    create_admin_user()
    app.run(debug=True)