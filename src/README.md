# osu! to Clone Hero Web Converter

A web application that allows users to convert timing points (BPM changes and time signatures) from osu! beatmaps to Clone Hero chart format.

## Features

- Web interface for the osuToCH conversion tool
- Direct download of osu! beatmaps from the official site
- Automatic extraction of timing data from .osu files
- Conversion of osu! timing points to Clone Hero format
- Display of beatmap metadata and conversion results
- Copy to clipboard functionality

## Requirements

- Python 3.6 or higher
- Flask and other dependencies (see requirements.txt)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/theyadev/osuToChTimings.git
   cd osuToChTimings/src
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Run the Flask application:

```bash
python app.py
```

The application will be available at http://127.0.0.1:5000/

## Deployment

For production deployment, consider using a proper WSGI server like Gunicorn or uWSGI, along with a reverse proxy like Nginx.

Example with Gunicorn:

1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Run with Gunicorn:
   ```bash
   gunicorn app:app -w 4 -b 0.0.0.0:8000
   ```

## API Usage

While this is primarily a web application, the core conversion functionality can be imported and used in other Python projects:

```python
from main import extract_timing_points, convert_to_clone_hero_format, generate_clone_hero_output

# Extract timing points from an osu! file
timing_points = extract_timing_points("path/to/beatmap.osu")

# Convert to Clone Hero format
ch_timing_lines = convert_to_clone_hero_format(timing_points, tick_rate=192)

# Generate the output string
output = generate_clone_hero_output(ch_timing_lines)
```

## License

This project is licensed under the MIT License - see the LICENSE file in the root directory for details. 