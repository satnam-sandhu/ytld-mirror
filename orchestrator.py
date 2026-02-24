import os
import sys
import subprocess

# Determine the absolute directory of the script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXEC = sys.executable

def run_script(script_name, args, capture_stdout=False):
    """Runs a python script. Optionally captures stdout."""
    script_path = os.path.join(SCRIPT_DIR, script_name)
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
    # Tracker can now return multiple file paths (one per line)
    tracker_output = run_script("yt_shorts_tracker.py", [channel_url], capture_stdout=True)
    
    if not tracker_output:
        # The tracker might have printed "No new shorts" to stderr
        return

    # Split output into individual file paths
    downloaded_files = [f.strip() for f in tracker_output.split("\n") if f.strip()]
    
    sys.stderr.write(f"Detected {len(downloaded_files)} new video(s).\n")

    for downloaded_file in downloaded_files:
        if not os.path.exists(downloaded_file):
            sys.stderr.write(f"Warning: File {downloaded_file} not found. Skipping.\n")
            continue

        sys.stderr.write(f"\n--- Processing: {downloaded_file} ---\n")
        
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
