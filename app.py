import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

TOKEN_MAX_AGE = 3600

db = SQLAlchemy(app)
migrate = Migrate(app, db)

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])


class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    subtitle = db.Column(db.String(200), nullable=True)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


def generate_token(user):
    return serializer.dumps({"user_id": user.id})


def get_current_user():
    token = session.get("auth_token")

    if not token:
        return None

    try:
        data = serializer.loads(token, max_age=TOKEN_MAX_AGE)
        return db.session.get(Users, data["user_id"])
    except (BadSignature, SignatureExpired, KeyError, TypeError):
        session.pop("auth_token", None)
        return None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if get_current_user() is None:
            flash("Пожалуйста, войдите в аккаунт.")
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Заполните все поля.")
            return render_template("register.html")

        existing_user = Users.query.filter(
            (Users.username == username) | (Users.email == email)
        ).first()

        if existing_user:
            flash("Такое имя пользователя или email уже зарегистрированы.")
            return render_template("register.html")

        user = Users(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash("Регистрация прошла успешно. Теперь войдите в аккаунт.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = Users.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["auth_token"] = generate_token(user)
            return redirect(url_for("diary"))

        flash("Неверный email или пароль.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("auth_token", None)
    flash("Вы вышли из аккаунта.")
    return redirect(url_for("login"))


@app.route("/notes", methods=["GET", "POST"])
@login_required
def diary():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        subtitle = request.form.get("subtitle", "").strip()
        content = request.form.get("content", "").strip()

        if title and content:
            new_note = Notes(
                title=title,
                subtitle=subtitle or None,
                text=content
            )

            db.session.add(new_note)
            db.session.commit()

        return redirect(url_for("diary"))

    notes = Notes.query.order_by(Notes.id.desc()).all()
    return render_template("notes.html", notes=notes)


if __name__ == "__main__":
    app.run(debug=True)