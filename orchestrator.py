import os
import sys
import subprocess

# Determine the absolute directory of the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXEC = sys.executable

def run_script(script_name, args, capture_stdout=False):
    """Runs a python script. Optionally captures stdout."""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    # Ensure all args are strings
    args = [str(a) for a in args]
    cmd = [PYTHON_EXEC, script_path] + args
    
    sys.stderr.write(f"--- Running {script_name} {' '.join(args)} ---\n")
    try:
        if capture_stdout:
            # We capture stdout but let stderr flow to the parent's stderr
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Forward stderr manually since we captured it
            sys.stderr.write(result.stderr)
            return result.stdout.strip()
        else:
            # Let everything flow to the parent's streams
            subprocess.run(cmd, check=True)
            return True
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running {script_name}: {e}\n")
        if capture_stdout:
            sys.stderr.write(f"Stderr: {e.stderr}\n")
        return None

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python orchestrator.py <channel_url>\n")
        sys.exit(1)
        
    channel_url = sys.argv[1]
    
    # 1. Run the tracker
    # Tracker now returns only the latest single file path
    downloaded_file = run_script("yt_shorts_tracker.py", [channel_url], capture_stdout=True)
    
    if not downloaded_file:
        # The tracker might have printed "No new shorts" to stderr
        return

    if not os.path.exists(downloaded_file):
        sys.stderr.write(f"Warning: File {downloaded_file} not found. Skipping.\n")
        return

    sys.stderr.write(f"New video downloaded: {downloaded_file}\n")
    
    # 2. Run the watermarker
    sys.stderr.write("Applying watermark...\n")
    run_script("watermark_video.py", [downloaded_file])
    
    # 3. Run the uploader
    sys.stderr.write("Uploading to YouTube...\n")
    video_title = os.path.splitext(os.path.basename(downloaded_file))[0]
    # We don't check for success here since upload might fail without client_secret
    run_script("upload_video.py", [downloaded_file, "--title", video_title])
        
    sys.stderr.write("\nOrchestration complete.\n")

if __name__ == "__main__":
    main()
