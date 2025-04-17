#!/usr/bin/env python3
"""
osu! to Clone Hero Web Converter

A web application that allows users to enter a link to an osu! beatmap,
downloads the beatmap, extracts the .osu file, and converts the timing points
to Clone Hero format.
"""

import os
import sys
import re
import requests
import zipfile
import io
import logging
import tempfile
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for

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

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size

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
    match = re.match(OSU_BEATMAP_URL_PATTERN, beatmap_url)
    if not match:
        flash('Invalid osu! beatmap URL. It should be in the format: https://osu.ppy.sh/beatmapsets/XXXXX')
        return redirect(url_for('index'))

    beatmap_id = match.group(1)
    download_url = f"https://beatconnect.io/b/{beatmap_id}"
    
    try:
        # Download the beatmap
        logger.info(f"Downloading beatmap from {download_url}")
        
        # Set headers for the request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        
        response = requests.get(download_url, headers=headers, stream=True)
        
        if response.status_code != 200:
            flash(f'Failed to download beatmap. Status code: {response.status_code}')
            return redirect(url_for('index'))
        
        # Create a temporary directory to extract files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the .osz file (which is just a zip)
            try:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
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
            
            # Extract the beatmap info for display
            beatmap_info = {}
            with open(osu_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract metadata
                try:
                    title_match = re.search(r'Title:(.*)', content)
                    artist_match = re.search(r'Artist:(.*)', content)
                    creator_match = re.search(r'Creator:(.*)', content)
                    version_match = re.search(r'Version:(.*)', content)
                    
                    if title_match:
                        beatmap_info['title'] = title_match.group(1).strip()
                    if artist_match:
                        beatmap_info['artist'] = artist_match.group(1).strip()
                    if creator_match:
                        beatmap_info['creator'] = creator_match.group(1).strip()
                    if version_match:
                        beatmap_info['version'] = version_match.group(1).strip()
                except Exception as e:
                    logger.error(f"Error extracting metadata: {str(e)}")
            
            # Convert the timing points
            try:
                timing_points = extract_timing_points(osu_file_path)
                logger.info(f"Found {len(timing_points)} timing points")
                
                ch_timing_lines = convert_to_clone_hero_format(timing_points)
                ch_output = generate_clone_hero_output(ch_timing_lines)
                
                return render_template(
                    'result.html', 
                    output=ch_output, 
                    beatmap_info=beatmap_info
                )
            except Exception as e:
                flash(f'Error converting timing points: {str(e)}')
                return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True) 