import os
import sys
import subprocess

# Determine the absolute directory of the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXEC = sys.executable

def run_script(script_name, args):
    """Runs a python script and returns its stdout."""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    cmd = [PYTHON_EXEC, script_path] + args
    
    sys.stderr.write(f"--- Running {script_name} {' '.join(args)} ---\n")
    try:
        # We capture stdout to get the filename from the tracker
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running {script_name}: {e}\n")
        sys.stderr.write(f"Stderr: {e.stderr}\n")
        return None

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python orchestrator.py <channel_url>\n")
        sys.exit(1)
        
    channel_url = sys.argv[1]
    
    # 1. Run the tracker
    downloaded_file = run_script("yt_shorts_tracker.py", [channel_url])
    
    if not downloaded_file or not os.path.exists(downloaded_file):
        sys.stderr.write("No new video to process.\n")
        return

    sys.stderr.write(f"New video downloaded: {downloaded_file}\n")
    
    # 2. Run the watermarker
    # Note: watermarker replaces the file in place
    sys.stderr.write("Applying watermark...\n")
    run_script("watermark_video.py", [downloaded_file])
    
    # 3. Run the uploader
    sys.stderr.write("Uploading to YouTube...\n")
    video_title = os.path.splitext(os.path.basename(downloaded_file))[0]
    run_script("upload_video.py", [downloaded_file, "--title", video_title])

if __name__ == "__main__":
    main()
