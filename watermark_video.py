import os
import sys
import subprocess
import shutil

FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"
WATERMARK_TEXT = "hecker boizz"

def add_watermark(input_path):
    """
    Adds a centered watermark with 20% transparency to a video and replaces the original.
    """
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} does not exist.")
        return False

    temp_output = input_path + ".tmp.mp4"
    
    # FFmpeg command:
    # x=(w-text_w)/2:y=(h-text_h)/2  -> centered
    # fontcolor=white@0.2            -> 20% transparency
    
    # We use -y to overwrite temp file if exists
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"drawtext=text='{WATERMARK_TEXT}':fontfile={FONT_PATH}:x=(w-text_w)/2:y=(h-text_h)/2:fontsize=48:fontcolor=white@0.2",
        "-codec:a", "copy",
        temp_output
    ]
    
    print(f"Applying watermark to: {input_path}")
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Replace original file
        os.remove(input_path)
        os.rename(temp_output, input_path)
        
        print(f"Successfully watermarked and replaced: {input_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error watermarking video: {e.stderr.decode()}")
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python watermark_video.py <video_path>")
        sys.exit(1)
        
    video_path = sys.argv[1]
    add_watermark(video_path)

if __name__ == "__main__":
    main()
