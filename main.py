from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, User, Task
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user
from fnmatch import fnmatch
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
    return render_template("index.html", topics=[1, 2])

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
            return render_template("register.htm", error="Пароль слишком короткий", username=username)
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

@app.route('/test/<int:topic>')
def test(topic):
    tasks = Task.query.filter_by(topic=topic).all()
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
    tasks_topic1 = Task.query.filter_by(topic=1).order_by(Task.id).all()
    tasks_topic2 = Task.query.filter_by(topic=2).order_by(Task.id).all()

    idx1 = (var_num - 1) % len(tasks_topic1)
    idx2 = (var_num - 1) % len(tasks_topic2)

    task1 = tasks_topic1[idx1]
    task2 = tasks_topic2[idx2]

    tasks = [task1, task2]

    return render_template('variant.html', tasks=tasks, var_num=var_num)


@app.route('/check_variant/<int:var_num>', methods=['POST'])
def check_variant(var_num):
    tasks_topic1 = Task.query.filter_by(topic=1).order_by(Task.id).all()
    tasks_topic2 = Task.query.filter_by(topic=2).order_by(Task.id).all()

    idx1 = (var_num - 1) % len(tasks_topic1)
    idx2 = (var_num - 1) % len(tasks_topic2)

    task1 = tasks_topic1[idx1]
    task2 = tasks_topic2[idx2]
    tasks = [task1, task2]

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

    return render_template('result.html', score=correct_count, results=results,
                           total=len(tasks), variant_id=var_num)

@app.route('/check/<int:topic>', methods=['POST'])
def check(topic):
    tasks = Task.query.filter_by(topic=topic).all()

    i = 0
    res = []

    for task in tasks:
        user_answer = request.form.get(f"answer_{task.id}")

        if user_answer:
            user_answer = user_answer.strip()

        correct = user_answer.replace(",", ".") == task.answer
        if correct:
            i += 1
        res.append({
            'question': task.question,
            'user_answer': user_answer,
            'correct_answer': task.answer,
            'is_correct': correct
        })
    return render_template('result.html', score=i, results=res)

if __name__ == '__main__':
    app.run(port=8080)
