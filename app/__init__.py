from flask import Flask
from flask_bootstrap import Bootstrap5
from app.database import init_db
import os

def create_app():
    app = Flask(__name__)
    Bootstrap5(app)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///lectures.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    
    # Ensure upload directories exist
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'transcriptions'), exist_ok=True)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)
    
    return app