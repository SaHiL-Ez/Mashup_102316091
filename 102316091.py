import sys
import os
import yt_dlp
from moviepy import AudioFileClip, concatenate_audioclips
import shutil

def download_and_convert(singer, n, output_dir="temp_downloads"):
    """
    Downloads N videos of the singer and converts them to audio.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Downloading {n} videos of {singer}...")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': True,
        'default_search': f"ytsearch{n}:{singer}" 
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch{n}:{singer}"])

    return output_dir

def process_audios(source_dir, duration, output_filename):
    """
    Cuts the first 'duration' seconds of each audio and merges them.
    """
    print(f"Processing audios: Cutting first {duration} seconds and merging...")
    
    audio_files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.endswith('.mp3')]
    clips = []
    # Keep track of all resources that need closing to prevent PermissionErrors
    resources_to_close = []

    try:
        for file in audio_files:
            try:
                clip = AudioFileClip(file)
                resources_to_close.append(clip)
                
                # Cut the first 'duration' seconds
                if clip.duration > duration:
                    # In moviepy v2, subclipped returns a new clip
                    sub_clip = clip.subclipped(0, duration)
                    clips.append(sub_clip)
                    resources_to_close.append(sub_clip) 
                else:
                     clips.append(clip)
            except Exception as e:
                print(f"Error processing {file}: {e}")

        if clips:
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
    if len(sys.argv) != 5:
        print("Usage: python <program.py> <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        print("Example: python 102316091.py \"Sharry Maan\" 20 20 102316091-output.mp3")
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

    # Main Logic
    temp_dir = "temp_mashup_files"
    
    try:
        download_and_convert(singer_name, num_videos, temp_dir)
        process_audios(temp_dir, audio_duration, output_file)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        clean_up(temp_dir)

if __name__ == "__main__":
    main()
