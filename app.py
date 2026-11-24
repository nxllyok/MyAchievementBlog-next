from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    subtitle = db.Column(db.String(200), nullable=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/notes", methods=["GET", "POST"])
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