from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from app.models import Class, Course, Lecture
from app.database import db
from app.transcriber import TranscriptionService
import soundfile as sf
import numpy as np
import subprocess
os.environ["FFMPEG_BINARY"] = r"C:\ffmpeg\bin\ffmpeg.exe"

from pydub import AudioSegment
import io

bp = Blueprint('main', __name__)
transcriber = TranscriptionService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'wav', 'mp3', 'm4a', 'ogg'}

@bp.route('/')
def index():
    recent_lectures = Lecture.query.order_by(Lecture.created_at.desc()).limit(5).all()
    return render_template('index.html', recent_lectures=recent_lectures)

@bp.route('/record')
def record():
    classes = Class.query.all()
    return render_template('record.html', classes=classes)

@bp.route('/upload')
def upload():
    classes = Class.query.all()
    return render_template('upload.html', classes=classes)

@bp.route('/manage')
def manage():
    classes = Class.query.all()
    return render_template('manage.html', classes=classes)

@bp.route('/api/courses/<int:class_id>')
def get_courses(class_id):
    courses = Course.query.filter_by(class_id=class_id).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in courses])

def convert_to_wav_ffmpeg(input_path, output_path):
    try:
        command = ['ffmpeg', '-y', '-i', input_path, output_path]  # -y overwrites existing files
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg conversion error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("FFmpeg not found. Please install FFmpeg.")
        return False
    
    
@bp.route('/api/save-recording', methods=['POST'])
def save_recording():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    course_id = request.form.get('course_id')
    chapter = request.form.get('chapter')
    name = request.form.get('name')
    
    if not all([audio_file, course_id, chapter, name]):
        return jsonify({'error': 'Missing required fields'}), 400

    filename = f"{uuid.uuid4()}.webm"  # Keep original filename for now
    input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
    audio_file.save(input_path)  # Save the original WebM file

    wav_filename = f"{filename.rsplit('.', 1)[0]}.wav"
    wav_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', wav_filename)

    if not convert_to_wav_ffmpeg(input_path, wav_path):
        os.remove(input_path)  # Clean up the original WebM
        return jsonify({'error': 'Error converting audio to WAV'}), 500
    
    os.remove(input_path) # remove the webm file

    # Now convert to mono
    mono_wav_filename = f"{wav_filename.rsplit('.', 1)[0]}_mono.wav"
    mono_wav_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', mono_wav_filename)
    if not convert_to_wav_ffmpeg(wav_path, mono_wav_path):
        os.remove(wav_path)
        return jsonify({'error': 'Error converting audio to mono'}), 500
    os.remove(wav_path)
    # Generate transcription (using the WAV path)
    trans_filename = f"{mono_wav_filename.rsplit('.', 1)[0]}.md"
    trans_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'transcriptions', trans_filename)

    try:
        transcriber.transcribe_file(mono_wav_path, trans_path)  # Use the WAV path
        # ... (Database update as before, using wav_path)
        lecture = Lecture(
            name=name,
            chapter=chapter,
            date=datetime.utcnow().date(),
            audio_path=mono_wav_path,
            transcription_path=trans_path,
            course_id=course_id,
            transcription_status='completed'
        )
        db.session.add(lecture)
        db.session.commit()
        return jsonify({'success': True, 'lecture_id': lecture.id})
    except Exception as e:
        print(f"Transcription error: {e}")
        return jsonify({'error': 'Error during transcription'}), 500
    
    
@bp.route('/api/upload-file', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('main.upload'))
    
    audio_file = request.files['audio']
    if not audio_file or not allowed_file(audio_file.filename):
        flash('Invalid file type', 'error')
        return redirect(url_for('main.upload'))
    
    try:
        # Save and process file similar to save-recording
        filename = secure_filename(f"{uuid.uuid4()}.{audio_file.filename.rsplit('.', 1)[1]}")
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
        audio_file.save(audio_path)
        
        # Create lecture record
        lecture = Lecture(
            name=request.form['name'],
            chapter=request.form['chapter'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            audio_path=audio_path,
            course_id=request.form['course_id'],
            transcription_status='pending'
        )
        db.session.add(lecture)
        db.session.commit()
        
        # Start transcription
        trans_filename = f"{filename.rsplit('.', 1)[0]}.md"
        trans_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'transcriptions', trans_filename)
        transcriber.transcribe_file(audio_path, trans_path)
        
        lecture.transcription_path = trans_path
        lecture.transcription_status = 'completed'
        db.session.commit()
        
        flash('File uploaded and transcribed successfully', 'success')
        return redirect(url_for('main.view_lecture', lecture_id=lecture.id))
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('main.upload'))

@bp.route('/lecture/<int:lecture_id>')
def view_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    
    # Read transcription file
    transcription = ''
    if lecture.transcription_path and os.path.exists(lecture.transcription_path):
        with open(lecture.transcription_path, 'r', encoding='utf-8') as f:
            transcription = f.read()
            
    return render_template('view_lecture.html', lecture=lecture, transcription=transcription)



