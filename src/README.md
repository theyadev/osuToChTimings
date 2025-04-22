# .osu to .chart Timing Web Converter

A web application that allows users to convert timing points (BPM changes and time signatures) from osu! beatmaps to Clone Hero chart format.

## Features

- Web interface for the .osu to .chart conversion tool
- Direct download of osu! beatmaps from the official site or beatconnect.io
- Automatic extraction of timing data from .osu files
- Conversion of osu! timing points to Clone Hero format
- Display of beatmap metadata and conversion results
- Download complete .chart files with proper metadata
- Download audio files extracted from beatmaps
- Copy to clipboard functionality
- Dark theme interface (default)
- Responsive design for mobile and desktop
- Handles negative timing points in osu! files
- Preserves decimal precision in BPM values

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

The application is configured for deployment on Vercel. The `vercel.json` file contains the necessary configuration.

## Common Issues

- **Bad beatmap quality**: If the original osu! beatmap has poor timing quality, these inaccuracies will be carried over to the .chart file; choose well-timed beatmaps for best results
- **Audio misalignment**: If the timing feels off in Clone Hero, ensure you're using the identical audio file from the osu! beatmap
- **Server limitations**: On the web version, very large beatmaps might time out or fail to process due to serverless function limits
- **Negative timing points**: The tool will handle negative timing points by moving them to tick 0, which might not be 100% accurate for complex beatmaps

## License

This project is licensed under the MIT License - see the LICENSE file in the root directory for details. 