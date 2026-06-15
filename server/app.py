from math import ceil

from flask import Flask, jsonify, request, session

from config import Config
from extensions import bcrypt, db, migrate
from models import Note, User


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    @app.get("/")
    def index():
        return jsonify({"message": "Session auth API is running"})

    @app.post("/signup")
    def signup():
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password")
        password_confirmation = data.get("password_confirmation")

        errors = []
        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        if password != password_confirmation:
            errors.append("Password confirmation must match password.")
        if User.query.filter_by(username=username).first():
            errors.append("Username is already taken.")

        if errors:
            return jsonify({"errors": errors}), 400

        user = User(username=username)
        try:
            user.password_hash = password
        except ValueError as exc:
            return jsonify({"errors": [str(exc)]}), 400

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        return jsonify(user.to_dict()), 201

    @app.post("/login")
    def login():
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if not user or not user.authenticate(password):
            return jsonify({"errors": ["Invalid username or password."]}), 401

        session["user_id"] = user.id
        return jsonify(user.to_dict()), 200

    @app.get("/check_session")
    def check_session():
        user = current_user()
        if not user:
            return jsonify({}), 200
        return jsonify(user.to_dict()), 200

    @app.delete("/logout")
    def logout():
        session.pop("user_id", None)
        return jsonify({}), 200

    @app.get("/notes")
    def notes_index():
        user = require_auth()
        if user is None:
            return jsonify({"errors": ["Unauthorized"]}), 401

        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 10)), 1), 50)

        pagination = (
            Note.query.filter_by(user_id=user.id)
            .order_by(Note.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return (
            jsonify(
                {
                    "data": [note.to_dict() for note in pagination.items],
                    "meta": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "total_pages": ceil(pagination.total / per_page)
                        if pagination.total
                        else 0,
                    },
                }
            ),
            200,
        )

    @app.post("/notes")
    def notes_create():
        user = require_auth()
        if user is None:
            return jsonify({"errors": ["Unauthorized"]}), 401

        data = request.get_json() or {}
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()

        errors = []
        if not title:
            errors.append("Title is required.")
        if not content:
            errors.append("Content is required.")

        if errors:
            return jsonify({"errors": errors}), 400

        note = Note(title=title, content=content, user_id=user.id)
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201

    @app.patch("/notes/<int:note_id>")
    def notes_update(note_id):
        user = require_auth()
        if user is None:
            return jsonify({"errors": ["Unauthorized"]}), 401

        note = Note.query.filter_by(id=note_id, user_id=user.id).first()
        if not note:
            return jsonify({"errors": ["Note not found"]}), 404

        data = request.get_json() or {}
        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                return jsonify({"errors": ["Title cannot be blank."]}), 400
            note.title = title

        if "content" in data:
            content = (data.get("content") or "").strip()
            if not content:
                return jsonify({"errors": ["Content cannot be blank."]}), 400
            note.content = content

        db.session.commit()
        return jsonify(note.to_dict()), 200

    @app.delete("/notes/<int:note_id>")
    def notes_delete(note_id):
        user = require_auth()
        if user is None:
            return jsonify({"errors": ["Unauthorized"]}), 401

        note = Note.query.filter_by(id=note_id, user_id=user.id).first()
        if not note:
            return jsonify({"errors": ["Note not found"]}), 404

        db.session.delete(note)
        db.session.commit()
        return jsonify({}), 200

    def current_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        return db.session.get(User, user_id)

    def require_auth():
        return current_user()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
