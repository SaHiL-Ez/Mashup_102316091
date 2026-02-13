# Mashup Generator

A powerful tool to create audio mashups from YouTube videos of your favorite singers. This project includes both a **Command Line Interface (CLI)** for advanced users and a **Streamlit Web Application** for an easy-to-use experience.

![Dashboard](image/final_image.png)

## Table of Contents
- [Assignment Overview](#assignment-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Program 1: Command Line Interface](#program-1-command-line-interface)
- [Program 2: Web Service](#program-2-web-service)
    - [How it Works](#how-it-works)
    - [Running the App](#running-the-app)
- [Deployment](#deployment)

---

## Assignment Overview

**Program 1**: A Python script (`102316091.py`) that:
1.  Takes keyword/singer name, number of videos (`N`), trim duration (`Y`), and output filename as arguments.
2.  Downloads `N` videos from YouTube.
3.  Converts them to audio.
4.  Cuts the first `Y` seconds from each.
5.  Merges them into a single file.

**Program 2**: A Web Interface (`102316091_app.py`) that:
1.  Provides a form to input parameters.
2.  Processes the mashup on the server.
3.  Sends the result via Email (optional) and allows direct Download.

---

## Prerequisites

1.  **Python 3.7+**
2.  **FFmpeg**: Required for audio processing. Ensure it is installed and added to your system PATH.
    -   *Windows*: Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add `bin` folder to Environment Variables.
    -   *Linux*: `sudo apt install ffmpeg`

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/mashup-repo.git
    cd mashup-repo
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## Program 1: Command Line Interface

The CLI tool allows you to generate mashups directly from your terminal.

**File**: `102316091.py`

### Usage
```bash
python 102316091.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>
```

### Parameters
-   `<SingerName>`: The artist to search for (e.g., "Sharry Mann").
-   `<NumberOfVideos>`: Number of videos to download. **Must be > 10**.
-   `<AudioDuration>`: Seconds to cut from the start of each video. **Must be >= 20**.
-   `<OutputFileName>`: Name of the final output file (e.g., `mashup.mp3`).

### Example
```bash
python 102316091.py "Sharry Mann" 11 20 "output.mp3"
```
*Successfully creates `output.mp3` in the current directory.*

---

## Program 2: Web Service

The web application provides a user-friendly interface to generate and download mashups.

**File**: `102316091_app.py`

### How it Works
The web service follows a strictly defined workflow to ensure a smooth user experience:

1.  **User Input**:
    *   **Singer Name**: Enter the name of the artist you want to create a mashup for.
    *   **Number of Videos**: Specify how many videos to fetch (Validation: Must be > 10).
    *   **Audio Duration**: Specify the duration in seconds to clip from each video (Validation: Must be >= 20).
    *   **Email Id**: Enter the recipient's email address.

2.  **Processing**:
    *   Upon clicking **Submit**, the backend triggers the mashup logic.
    *   It searches YouTube for the specified number of videos.
    *   Downloads the audio streams.
    *   Trims the first `Y` seconds from each audio file.
    *   Merges all clips into a single continuous audio track.

3.  **Output & Delivery**:
    *   **Zip Creation**: The final audio file is compressed into a ZIP archive (`mashup_output.zip`).
    *   **Email Delivery (Optional)**: If selected, the ZIP file is emailed to the provided address using SMTP.
    *   **Direct Download**: A **"Download Zip"** button appears, allowing you to save the file locally to your computer immediately.

### Running the App Locally

Start the Streamlit server:
```bash
streamlit run 102316091_app.py
```
Open your browser at `http://localhost:8501`.

---

## Deployment

To deploy this app on **Streamlit Cloud**:

1.  Push your code to a GitHub repository.
2.  Login to [share.streamlit.io](https://share.streamlit.io).
3.  Deploy the app by selecting your repository and `102316091_app.py`.
4.  **Configuration**:
    -   The app requires **FFmpeg**. This is handled by the `packages.txt` file included in the repo.
    -   **Secrets**: For email functionality, go to App Settings -> Secrets and add:
        ```toml
        EMAIL_SENDER = "your_email@gmail.com"
        EMAIL_PASSWORD = "your_app_password"
        ```

![Final Result](image/final_image.png)
