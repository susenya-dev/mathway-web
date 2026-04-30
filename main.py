import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, User, Task
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from fnmatch import fnmatch

import uuid
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'secretkey'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 


@app.route('/')
def home():
    return render_template("index.html", topics=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])


@app.route('/profile')
def profile():
    """Шаблон профиля"""
    return render_template("profile.html")


@app.route('/logout')
def logout():
    """разлогин"""
    logout_user()
    return redirect(url_for('login'))


@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Сохранение аватарок в бд в профиль"""
    file = request.files['avatar']

    # пользователь
    user = User.query.get(current_user.id)

    # удаление старой авы
    if user.avatar and user.avatar != "avatars/none_avatar.jpg":
        old_path = os.path.join("static", user.avatar)
        if os.path.exists(old_path):
            os.remove(old_path)

    # новый аватар с уник именем
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"

    path = f"avatars/{filename}"
    file.save(os.path.join("static", path))
    user.avatar = path
    db.session.commit()

    return redirect(url_for('profile'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        confirm_password = request.form["confirm_password"]

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Пользователь уже существует", username=username)
        if confirm_password != password:
            return render_template("register.html", error="Пароли не совпадают", username=username)
        if len(password) < 6:
            return render_template("register.html", error="Пароль слишком короткий", username=username)
        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="Электронная почта уже занята", username=username)
        if not fnmatch(email, "*@*.*"):
            return render_template("register.html", error="Неправильная запись почты", username=username)
        hashed_password = generate_password_hash(password)

        user = User(username=username, password=hashed_password, email=email)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Неверный логин или пароль", username=username)

    return render_template('login.html')


# @app.route('/test')
# def test():
#     tasks = Task.query.all()
#     return render_template('test.html', tasks=tasks)

# @app.route('/test/<int:topic>')
# def test(topic):
#     tasks = Task.query.filter_by(topic=topic).all()
#     return render_template('test.html', tasks=tasks, topic=topic)


@app.route('/test/<int:topic>')
def test(topic):
    res = requests.get('http://127.0.0.1:8080/api/tasks')
    tasks = res.json()

    tasks = [t for t in tasks if int(t['topic']) == topic]

    return render_template('test.html', tasks=tasks, topic=topic)

@app.route('/api/tasks')
def api_tasks():
    tasks = Task.query.all()

    result = []
    for t in tasks:
        result.append({
            'id': t.id,
            'question': t.question,
            'topic': t.topic,
            'image_url': t.image_url
        })

    return jsonify(result)


@app.route('/variant/<int:var_num>')
def variant(var_num):
    """
    Создание варианта
    :param var_num: номер варианта
    :return:
    """
    tasks = []
    for i in range(1, 13):
        tasks_topic = Task.query.filter_by(topic=i).order_by(Task.id).all()
        idx = (var_num - 1) % len(tasks_topic)
        task = tasks_topic[idx]
        tasks.append(task)

    return render_template('variant.html', tasks=tasks, var_num=var_num)


@app.route('/check_variant/<int:var_num>', methods=['POST'])
def check_variant(var_num):
    """
    варианты ответ
    :param var_num:
    :return:
    """

    tasks = []
    for i in range(1, 13):
        tasks_topic = Task.query.filter_by(topic=i).order_by(Task.id).all()
        idx = (var_num - 1) % len(tasks_topic)
        task = tasks_topic[idx]
        tasks.append(task)

    correct_count = 0
    results = []

    for task in tasks:
        user_answer = request.form.get(f"answer_{task.id}")
        if user_answer:
            user_answer = user_answer.strip()

        is_correct = user_answer.replace(",", ".") == task.answer
        if is_correct:
            correct_count += 1

        results.append({
            'question': task.question,
            'user_answer': user_answer,
            'correct_answer': task.answer,
            'is_correct': is_correct
        })

    current_user.count_task += correct_count
    db.session.commit()

    return render_template('result.html', score=correct_count, results=results,
                           total=len(tasks), variant_id=var_num)


@app.route('/check/<int:topic>', methods=['POST'])
@login_required
def check(topic):
    tasks = Task.query.filter_by(topic=topic).all()

    correct_count = 0
    res = []

    for task in tasks:
        user_answer = request.form.get(f"answer_{task.id}")

        if user_answer:
            user_answer = user_answer.strip()

        correct = user_answer.replace(",", ".") == task.answer
        if correct:
            correct_count += 1

        res.append({
            'question': task.question,
            'user_answer': user_answer,
            'correct_answer': task.answer,
            'is_correct': correct
        })


    current_user.count_task += correct_count
    db.session.commit()

    return render_template('result.html', score=correct_count, results=res)

if __name__ == '__main__':
    app.run(port=8080)
