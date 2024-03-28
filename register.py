from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint
import psycopg2
from bd import conn, cursor  # Импортируйте соединение и курсор из bd.py

app = Flask(__name__)

user_register = Blueprint('user_register', __name__)

# Роут для регистрации пользователя
@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Проверяем, что пользователь с таким логином не существует
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('register'))

        # Создаем нового пользователя
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        flash('Вы успешно зарегистрировались', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)