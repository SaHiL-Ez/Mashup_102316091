# Mashup Assignment

This project provides a tool to download videos from YouTube for a specific singer, convert them to audio, cut the first few seconds, and merge them into a single mashup file. It includes both a Command Line Interface (CLI) and a Web Interface using Streamlit.

## Features
- **Download**: Fetches videos from YouTube.
- **Convert & Cut**: Extracts audio and trims the start.
- **Merge**: Concatenates clips into a single audio file.
- **Web UI**: User-friendly interface with Email functionality.

## Prerequisites

1.  **Python**: Ensure Python is installed.
2.  **FFmpeg**: Ensure FFmpeg is installed and added to your system PATH (required for `moviepy`).
3.  **Dependencies**: Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## 1. CLI Usage (`102316091.py`)

### Command Format
```bash
python 102316091.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>
```

### Constraints
- **NumberOfVideos**: Must be greater than 10.
- **AudioDuration**: Must be greater than or equal to 20.

### Example
To create a mashup of "Tom Misch" with 11 videos, each cut to 20 seconds:
```bash
python 102316091.py "Tom Misch" 11 20 "mashup.mp3"
```
The output file `mashup.mp3` will be saved in the current directory.

## 2. Web Service Usage (`102316091_app.py`)

### Running the App
Run the Streamlit app with the following command:
```bash
streamlit run 102316091_app.py
```

### Using the Interface
1.  Open the URL provided in the terminal (usually `http://localhost:8501`).
2.  Fill in the form:
    - **Singer Name**: Name of the artist.
    - **Number of Videos**: Minimum 11.
    - **Audio Duration**: Minimum 20 seconds.
    - **Email Id**: Your email address to receive the mashup.
3.  Click **Submit**.
