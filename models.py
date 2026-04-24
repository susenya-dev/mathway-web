from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    # status = db.Column(db.Integer,)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(10), nullable=False)

    image_url = db.Column(db.String(255))