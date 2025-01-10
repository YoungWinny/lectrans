from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
import os


# Create database instance
db = SQLAlchemy()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def init_db(app):
    """Initialize the database and create tables"""
    db.init_app(app)
    
    # Ensure uploads directory exists
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'audio'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'transcriptions'), exist_ok=True)
    
    with app.app_context():
        db.create_all()

def reset_db(app):
    """Reset the database (for development only)"""
    with app.app_context():
        db.drop_all()
        db.create_all()
