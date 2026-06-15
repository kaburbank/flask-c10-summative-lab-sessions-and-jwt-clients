"""Database seeding script for development and testing.

Creates sample users and notes to populate the database.
"""

from app import app
from extensions import db
from models import Note, User


def seed():
    """Clear existing data and create sample users and notes.
    
    Creates two users (alice, bob) with sample notes to test the API.
    """
    with app.app_context():
        Note.query.delete()
        User.query.delete()

        user_1 = User(username="alice")
        user_1.password_hash = "password123"

        user_2 = User(username="bob")
        user_2.password_hash = "password123"

        db.session.add_all([user_1, user_2])
        db.session.flush()

        notes = [
            Note(title="Groceries", content="Milk, eggs, bread", user_id=user_1.id),
            Note(title="Workout", content="Push day: bench and rows", user_id=user_1.id),
            Note(title="Ideas", content="Build a habit tracker", user_id=user_2.id),
        ]

        db.session.add_all(notes)
        db.session.commit()
        print("Seed complete: users and notes created.")


if __name__ == "__main__":
    seed()
