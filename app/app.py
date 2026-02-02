import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

db = SQLAlchemy()

def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    class User(db.Model):
        __tablename__ = "users"
        id = db.Column(db.BigInteger, primary_key=True)
        username = db.Column(db.Text, unique=True, nullable=False)
        password_hash = db.Column(db.Text, nullable=False)

    with app.app_context():
        required = {"users", "images"}
        rows = db.session.execute(
            text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public';")
        ).fetchall()
        existing = {r[0] for r in rows}
        missing = required - existing
        if missing:
            raise RuntimeError(
                f"Missing DB tables: {sorted(missing)}. Run DB setup first."
            )
    def require_login():
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return None

    @app.get("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("profile"))
        return redirect(url_for("login"))

    @app.get("/profile")
    def profile():
        r = require_login()
        if r:
            return r
        return render_template("profile.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""

            if not username or not password:
                flash("Username and password are required.")
                return render_template("register.html")

            existing = User.query.filter_by(username=username).first()
            if existing:
                flash("Username already exists.")
                return render_template("register.html")

            u = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(u)
            db.session.commit()

            session["user_id"] = int(u.id)
            return redirect(url_for("profile"))
        return render_template ("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""

            u = User.query.filter_by(username=username).first()
            if not u or not check_password_hash(u.password_hash, password):
                flash("Invalid credentials")
                return render_template("login.html")

            session["user_id"] = int(u.id)
            return redirect(url_for("profile"))
        return render_template("login.html")

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

