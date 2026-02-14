import sys
import os
import yt_dlp
from moviepy import AudioFileClip, concatenate_audioclips
import shutil
import concurrent.futures
import queue
import threading

def download_one(url, output_dir, max_retries=3):
    """
    Helper function to download a single video with retry logic and anti-bot measures.
    """
    import time
    import random
    
    # Try to get YouTube tokens from environment (set by Streamlit Secrets)
    po_token = os.environ.get('YOUTUBE_PO_TOKEN', '')
    visitor_data = os.environ.get('YOUTUBE_VISITOR_DATA', '')
    
    # Build extractor args for YouTube
    youtube_extractor_args = {
        'player_client': ['android', 'android_music'],  # Android client has better format support
        'skip': ['hls', 'dash', 'translated_subs']
    }
    
    # Add tokens if available
    if po_token:
        youtube_extractor_args['po_token'] = po_token
        print(f"Using po_token for authentication (length: {len(po_token)})")
    if visitor_data:
        youtube_extractor_args['visitor_data'] = visitor_data
        print(f"Using visitor_data for authentication (length: {len(visitor_data)})")
    
    ydl_opts = {
        # Use simpler format string - let yt-dlp choose best available audio
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        # Android client headers
        'http_headers': {
            'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12; GB) gzip',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        },
        # YouTube-specific extractor args with tokens
        'extractor_args': {
            'youtube': youtube_extractor_args
        },
        # No rate limiting for local speed (set to 0 for maximum speed)
        'sleep_interval': 0,
        'max_sleep_interval': 0,
        'sleep_interval_requests': 0,
        # Additional options
        'age_limit': None,
        'nocheckcertificate': True,
    }
    
    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            # Add random delay between retries to avoid rate limiting
            if attempt > 0:
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"Retry {attempt + 1}/{max_retries} for {url} after {delay:.1f}s delay...")
                time.sleep(delay)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
            
        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                # Check if it's a retryable error
                if '403' in error_msg or 'Forbidden' in error_msg or 'HTTP Error' in error_msg:
                    print(f"Download attempt {attempt + 1} failed for {url}: {error_msg}")
                    continue
                else:
                    # Non-retryable error, fail immediately
                    print(f"Non-retryable error for {url}: {error_msg}")
                    return False
            else:
                print(f"Failed to download {url} after {max_retries} attempts: {error_msg}")
                return False
    
    return False

def download_and_convert(singer, n, output_dir="temp_downloads"):
    """
    Downloads N videos of the singer and converts them to audio concurrently.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Searching for {n} videos of {singer}...")
    
    # 1. Fetch URLs first
    search_opts = {
        'quiet': True,
        'extract_flat': True, 
        'default_search': f"ytsearch{n}:{singer}",
        'noplaylist': True,
    }
    
    urls = []
    
    try:
        # Get Info
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{n}:{singer}", download=False)
            if 'entries' in info:
                urls = [entry['url'] for entry in info['entries']]
                
        print(f"Found {len(urls)} videos. Starting PIPELINE: Download → Process simultaneously...")

        # PIPELINE PROCESSING: Download and process concurrently
        # Use a queue to feed downloaded files directly to processing
        file_queue = queue.Queue()
        processed_clips = []
        processing_lock = threading.Lock()
        successful_downloads = 0
        download_lock = threading.Lock()
        
        def process_worker(duration):
            """Worker thread that processes files as they arrive in queue"""
            while True:
                try:
                    file_path = file_queue.get(timeout=1)
                    if file_path is None:  # Poison pill to stop
                        break
                    
                    # Process the audio file immediately
                    try:
                        clip = AudioFileClip(file_path)
                        if clip.duration > duration:
                            cut_clip = clip.subclipped(0, duration)
                        else:
                            cut_clip = clip
                        
                        with processing_lock:
                            processed_clips.append(cut_clip)
                        print(f"  ⚡ Processed: {os.path.basename(file_path)} ({len(processed_clips)} ready)")
                    except Exception as e:
                        print(f"  ✗ Processing error for {os.path.basename(file_path)}: {e}")
                    finally:
                        file_queue.task_done()
                except queue.Empty:
                    continue
        
        # Start processing workers
        num_process_workers = 11
        process_threads = []
        for _ in range(num_process_workers):
            t = threading.Thread(target=process_worker, args=(duration,), daemon=True)
            t.start()
            process_threads.append(t)
        
        def download_and_queue(url):
            """Download and immediately queue for processing"""
            nonlocal successful_downloads
            if download_one(url, output_dir):
                with download_lock:
                    successful_downloads += 1
                # Find the newly downloaded file
                mp3_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.mp3')]
                if mp3_files:
                    # Get the most recent file
                    latest_file = max(mp3_files, key=os.path.getctime)
                    file_queue.put(latest_file)
                    print(f"✓ Downloaded {successful_downloads}/{len(urls)} → Queued for processing")
                return True
            else:
                print(f"✗ Download failed")
                return False
        
        # Download in parallel, each download queues file for immediate processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(download_and_queue, url) for url in urls]
            concurrent.futures.wait(futures)
        
        # Signal processing workers to stop
        for _ in range(num_process_workers):
            file_queue.put(None)
        
        # Wait for all processing to complete
        for t in process_threads:
            t.join()
        
        print(f"✅ Pipeline complete: {successful_downloads} downloads, {len(processed_clips)} processed")
        
        if successful_downloads == 0:
            raise Exception("No videos were downloaded successfully. Please check your internet connection or try again later.")
        
        # Store processed clips for merging (skip the separate process_audios call)
        return output_dir, processed_clips
             
    except Exception as e:
        print(f"Error during search/download: {e}")
        raise

    return output_dir

def process_one_audio(file_path, duration):
    """
    Helper to process a single audio file (load and cut).
    Returns the successfully processed clip or None.
    """
    try:
        clip = AudioFileClip(file_path)
        if clip.duration > duration:
            return clip.subclipped(0, duration)
        else:
            return clip
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def process_audios(source_dir, duration, output_filename):
    """
    Cuts the first 'duration' seconds of each audio and merges them using parallel processing.
    """
    print(f"Processing audios: Cutting first {duration} seconds and merging...")
    
    audio_files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.endswith('.mp3')]
    clips = []
    resources_to_close = []

    # Use ThreadPoolExecutor for processing (creating clips)
    # Note: MoviePy might have thread safety issues with some backends, 
    # but for simple cutting it should be fine.
    # We collect results ensuring order is implicitly consistent or doesn't matter (mashup order usually random or sorted by filename)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=11) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_one_audio, f, duration): f for f in audio_files}
        
        for future in concurrent.futures.as_completed(future_to_file):
            clip = future.result()
            if clip:
                clips.append(clip)
                resources_to_close.append(clip)

    try:
        if clips:
            print(f"Merging {len(clips)} clips...")
            final_clip = concatenate_audioclips(clips)
            resources_to_close.append(final_clip)
            final_clip.write_audiofile(output_filename)
            print(f"Mashup saved to {output_filename}")
        else:
            print("No audio clips to merge.")
            
    finally:
        # Close all resources safely
        for resource in resources_to_close:
            try:
                resource.close()
            except Exception:
                pass

def clean_up(directory):
    """
    Removes the temporary directory.
    """
    if os.path.exists(directory):
        shutil.rmtree(directory)
        print(f"Cleaned up temporary directory: {directory}")

def main():
    # Check for correct number of parameters
    # Usage: python <program.py> <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>
    if len(sys.argv) != 5:
        print("Usage: python 102316091.py <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        sys.exit(1)

    singer_name = sys.argv[1]
    try:
        num_videos = int(sys.argv[2])
        audio_duration = int(sys.argv[3])
    except ValueError:
        print("Error: NumberOfVideos and AudioDuration must be integers.")
        sys.exit(1)
        
    output_file = sys.argv[4]

    # Input Validation
    if num_videos <= 10:
        print("Error: NumberOfVideos must be greater than 10.")
        sys.exit(1)
    
    if audio_duration < 20:
        print("Error: AudioDuration must be greater than or equal to 20.")
        sys.exit(1)

    main(singer_name, num_videos, audio_duration, output_file)
