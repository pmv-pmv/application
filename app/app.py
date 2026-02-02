import os
import uuid
from pathlib import Path
from flask import Flask, render_template, request, redirect, session, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text

db = SQLAlchemy()

def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL isn't seyt. Run this app on app VM with Postgres")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["UPLOAD_ROOT"] = os.environ.get(
            "UPLOAD_ROOT", "/var/lib/pictapp/uploads"
    )

    db.init_app(app)

    class User(db.Model):
        __tablename__ = "users"
        id = db.Column(db.BigInteger, primary_key=True)
        username = db.Column(db.Text, unique=True, nullable=False)
        password_hash = db.Column(db.Text, nullable=False)

    class Image(db.Model):
        __tablename__ = "images"
        id = db.Column(db.BigInteger, primary_key=True)
        user_id = db.Column(db.BigInteger, nullable=False, index=True)
        original_filename = db.Column(db.Text, nullable=False)
        stored_filename = db.Column(db.Text, nullable=False, unique=True)
        stored_path = db.Column(db.Text, nullable=False)
        created_at = db.Column(db.DateTime(timezone=True), server_default=text("now()"), nullable=False)

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

    ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

    def upload_root() -> Path:
        return Path(app.config["UPLOAD_ROOT"])

    def user_upload_dir(user_id: int) -> Path:
        return upload_root() / f"u{user_id}"

    def pick_ext(filename: str) -> str:
        safe = secure_filename(filename or "")
        ext = Path(safe).suffix.lower()
        if ext not in ALLOWED_EXT:
            raise ValueError("Unsupported file type. Usr jpg,jpeg,png,webp")
        return ext

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

