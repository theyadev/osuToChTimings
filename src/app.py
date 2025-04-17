#!/usr/bin/env python3
"""
Beatmap to Chart Converter

A web application that allows users to enter a link to an osu! beatmap,
downloads the beatmap, extracts the .osu file, and converts the timing points
to Clone Hero chart format.
"""

import os
import sys
import re
import requests
import zipfile
import io
import logging
import tempfile
import shutil
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file, session
import time

# Add parent directory to path so we can import the conversion code
# This approach works for local development
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(os.path.join(parent_dir, 'main.py')):
    sys.path.append(parent_dir)
    from main import extract_timing_points, convert_to_clone_hero_format, generate_clone_hero_output
else:
    # For Vercel deployment - main.py should be copied to the same directory
    from conversion import extract_timing_points, convert_to_clone_hero_format, generate_clone_hero_output

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Constants
OSU_BEATMAP_URL_PATTERN = r'https?://osu\.ppy\.sh/beatmapsets/(\d+)(?:#.+)?'
BEATCONNECT_URL_PATTERN = r'https?://beatconnect\.io/b/(\d+)(?:/?.*)?'

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size

# Use in-memory storage for files in production (Vercel)
if os.environ.get('VERCEL', False):
    temp_base_dir = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = temp_base_dir
else:
    # In development, use a persistent folder
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    # Ensure the upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store audio file data in session for Vercel environment
session_files = {}

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    """Process the beatmap link and convert timing points."""
    beatmap_url = request.form.get('beatmap_url', '').strip()

    if not beatmap_url:
        flash('Please enter a beatmap URL')
        return redirect(url_for('index'))

    # Validate the URL
    beatmap_id = None
    if re.match(BEATCONNECT_URL_PATTERN, beatmap_url):
        beatmap_id = re.match(BEATCONNECT_URL_PATTERN, beatmap_url).group(1)
    elif re.match(OSU_BEATMAP_URL_PATTERN, beatmap_url):
        beatmap_id = re.match(OSU_BEATMAP_URL_PATTERN, beatmap_url).group(1)
    else:
        flash('Invalid beatmap URL. Please use a URL from osu! or beatconnect.io')
        return redirect(url_for('index'))

    fallback_url = f"https://beatconnect.io/b/{beatmap_id}"
    download_url = f"https://nerinyan.moe/d/{beatmap_id}"
    
    try:
        # Download the beatmap
        logger.info(f"Downloading beatmap from {download_url}")
        
        # osu! website requires a user agent and referer to be set
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Referer': f'https://osu.ppy.sh/beatmapsets/{beatmap_id}'
        }
        
        response = requests.get(download_url, headers=headers, stream=True)

        # If the beatmap is not found, try the fallback URL
        if response.status_code == 404:
            logger.info(f"Beatmap not found at {download_url}, trying fallback URL {fallback_url}")
            response = requests.get(fallback_url, headers=headers, stream=True)
        
        if response.status_code != 200:
            flash(f'Failed to download beatmap. Status code: {response.status_code}')
            return redirect(url_for('index'))

        # Create a unique session ID for this download
        session_id = os.urandom(16).hex()
        
        # Create a temporary directory to extract and process files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the downloaded file to the temporary directory
            osz_path = os.path.join(temp_dir, f"{beatmap_id}.osz")
            with open(osz_path, 'wb') as f:
                f.write(response.content)
            
            # Extract the .osz file (which is just a zip)
            try:
                with zipfile.ZipFile(osz_path) as zip_ref:
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile:
                flash('The downloaded file is not a valid .osz file')
                return redirect(url_for('index'))
            
            # Find the first .osu file
            osu_files = [f for f in os.listdir(temp_dir) if f.endswith('.osu')]
            if not osu_files:
                flash('No .osu files found in the beatmap')
                return redirect(url_for('index'))
            
            osu_file_path = os.path.join(temp_dir, osu_files[0])
            
            # Extract the beatmap info for display and get audio filename
            beatmap_info = {}
            audio_filename = None
            
            with open(osu_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract metadata
                try:
                    title_match = re.search(r'Title:(.*)', content)
                    artist_match = re.search(r'Artist:(.*)', content)
                    creator_match = re.search(r'Creator:(.*)', content)
                    version_match = re.search(r'Version:(.*)', content)
                    audio_match = re.search(r'AudioFilename:(.*)', content)
                    
                    if title_match:
                        beatmap_info['title'] = title_match.group(1).strip()
                    if artist_match:
                        beatmap_info['artist'] = artist_match.group(1).strip()
                    if creator_match:
                        beatmap_info['creator'] = creator_match.group(1).strip()
                    if version_match:
                        beatmap_info['version'] = version_match.group(1).strip()
                    if audio_match:
                        audio_filename = audio_match.group(1).strip()
                except Exception as e:
                    logger.error(f"Error extracting metadata: {str(e)}")
            
            # If we found an audio file, store it in memory for Vercel or in the session dir for local
            has_audio = False
            if audio_filename and os.path.exists(os.path.join(temp_dir, audio_filename)):
                audio_src_path = os.path.join(temp_dir, audio_filename)
                
                # For Vercel: store in memory
                if os.environ.get('VERCEL', False):
                    with open(audio_src_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                        session_files[session_id] = {
                            'filename': audio_filename,
                            'data': audio_data,
                            'timestamp': time.time()
                        }
                else:
                    # For local: store in uploads directory
                    session_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
                    os.makedirs(session_dir, exist_ok=True)
                    audio_dest_path = os.path.join(session_dir, audio_filename)
                    shutil.copy2(audio_src_path, audio_dest_path)
                
                has_audio = True
                session['audio_filename'] = audio_filename
                session['session_id'] = session_id
            
            # Convert the timing points
            try:
                timing_points = extract_timing_points(osu_file_path)
                logger.info(f"Found {len(timing_points)} timing points")
                
                ch_timing_lines = convert_to_clone_hero_format(timing_points)
                ch_output = generate_clone_hero_output(ch_timing_lines)
                
                return render_template(
                    'result.html', 
                    output=ch_output, 
                    beatmap_info=beatmap_info,
                    has_audio=has_audio,
                    audio_filename=audio_filename
                )
            except Exception as e:
                flash(f'Error converting timing points: {str(e)}')
                return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download_audio')
def download_audio():
    """Download the audio file from the extracted beatmap."""
    session_id = session.get('session_id')
    audio_filename = session.get('audio_filename')
    
    if not session_id or not audio_filename:
        flash('Audio file not available')
        return redirect(url_for('index'))
    
    # Check if we're using in-memory storage (Vercel)
    if os.environ.get('VERCEL', False):
        if session_id in session_files and 'data' in session_files[session_id]:
            audio_data = session_files[session_id]['data']
            return send_file(
                io.BytesIO(audio_data),
                mimetype='application/octet-stream',
                as_attachment=True,
                download_name=audio_filename
            )
        else:
            flash('Audio file not found')
            return redirect(url_for('index'))
    else:
        # Using file system storage
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id, audio_filename)
        
        if not os.path.exists(audio_path):
            flash('Audio file not found')
            return redirect(url_for('index'))
        
        return send_file(audio_path, as_attachment=True, download_name=audio_filename)

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@app.route('/robots.txt')
def robots():
    """Serve robots.txt from static directory."""
    return send_file('static/robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    """Serve sitemap.xml from static directory."""
    return send_file('static/sitemap.xml')

# Cleanup function to remove old files (only needed for local development)
def cleanup_old_files():
    """Clean up files older than 1 hour"""
    if os.environ.get('VERCEL', False):
        # On Vercel, cleanup temp files from memory
        current_time = time.time()
        to_remove = []
        for session_id, file_info in session_files.items():
            if 'timestamp' in file_info and current_time - file_info['timestamp'] > 3600:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del session_files[session_id]
        
        return
        
    import time
    current_time = time.time()
    uploads_folder = app.config['UPLOAD_FOLDER']
    
    for session_folder in os.listdir(uploads_folder):
        session_path = os.path.join(uploads_folder, session_folder)
        if os.path.isdir(session_path):
            # If folder is older than 1 hour
            if current_time - os.path.getctime(session_path) > 3600:
                try:
                    shutil.rmtree(session_path)
                    logger.info(f"Cleaned up old session folder: {session_folder}")
                except Exception as e:
                    logger.error(f"Error cleaning up folder {session_folder}: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True) 