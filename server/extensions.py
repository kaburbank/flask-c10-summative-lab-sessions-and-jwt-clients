from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Centralized extension instances to avoid circular imports.
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
