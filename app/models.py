from datetime import datetime
from app.database import db

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    courses = db.relationship('Course', backref='class', lazy=True, cascade='all, delete-orphan')

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    instructor = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lectures = db.relationship('Lecture', backref='course', lazy=True, cascade='all, delete-orphan')

class Lecture(db.Model):
    __tablename__ = 'lectures'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    chapter = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer)  # Duration in seconds
    audio_path = db.Column(db.String(500), nullable=False)
    transcription_path = db.Column(db.String(500))
    transcription_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, error
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)