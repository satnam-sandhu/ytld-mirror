import os
import sys
import subprocess
import json

# Determine the absolute directory of the script for cron compatibility
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "processed_shorts.json")
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "downloads")

def normalize_url(url):
    """
    Normalizes the channel URL by removing trailing slashes and /shorts suffix.
    """
    url = url.strip().rstrip("/")
    if url.endswith("/shorts"):
        url = url[:-7].rstrip("/")
    return url

def get_recent_short_ids(channel_url, limit=5):
    """
    Uses yt-dlp to get the IDs of the most recent shorts.
    """
    sys.stderr.write(f"Checking for recent shorts on: {channel_url}\n")
    
    shorts_url = channel_url + "/shorts"
    
    cmd = [
        "yt-dlp",
        "--get-id",
        "--playlist-items", str(limit),
        "--flat-playlist",
        shorts_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Returns a list of IDs (one per line)
        ids = [i.strip() for i in result.stdout.strip().split("\n") if i.strip()]
        return ids
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error fetching channel data: {e.stderr}\n")
        return []

def download_short(video_id):
    """
    Downloads a short given its video ID and returns the file path.
    """
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    url = f"https://www.youtube.com/shorts/{video_id}"
    sys.stderr.write(f"Downloading new short: {url}\n")
    
    # Use --get-filename to predict the output filename
    filename_cmd = [
        "yt-dlp",
        "--get-filename",
        "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        url
    ]
    
    try:
        # Get the filename first
        filename_result = subprocess.run(filename_cmd, capture_output=True, text=True, check=True)
        target_file = filename_result.stdout.strip()
        
        # Now download
        download_cmd = [
            "yt-dlp",
            "-q", # Quiet mode to keep stdout clean
            "-o", target_file,
            url
        ]
        # Run download and redirect stdout to stderr just in case
        subprocess.run(download_cmd, check=True, stdout=sys.stderr)
        sys.stderr.write("Download complete.\n")
        return target_file
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error downloading video: {e}\n")
        return None

def load_state():
    """Loads the JSON state file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            sys.stderr.write(f"Warning: Could not parse {STATE_FILE}. Starting fresh.\n")
            return {}
    return {}

def save_state(state):
    """Saves the state mapping to JSON."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python yt_shorts_tracker.py <channel_url>\n")
        sys.exit(1)
        
    channel_url = normalize_url(sys.argv[1])
    
    # 1. Get recent short IDs
    recent_ids = get_recent_short_ids(channel_url, limit=5)
    
    if not recent_ids:
        sys.stderr.write(f"No shorts found on {channel_url}.\n")
        return None

    # 2. Load state
    state = load_state()
    processed_ids = state.get(channel_url, [])
    if isinstance(processed_ids, str): # Handle old format (single string)
        processed_ids = [processed_ids]
            
    # 3. Find IDs that haven't been processed
    new_ids = [rid for rid in recent_ids if rid not in processed_ids]
    
    if not new_ids:
        sys.stderr.write(f"No new shorts found for {channel_url}.\n")
        return None
    
    sys.stderr.write(f"Found {len(new_ids)} new shorts for {channel_url}.\n")
    
    downloaded_files = []
    # Process from oldest to newest among the new ones
    for vid in reversed(new_ids):
        downloaded_file = download_short(vid)
        if downloaded_file:
            processed_ids.append(vid)
            # Clip the list to keep it manageable (e.g., last 50 IDs)
            processed_ids = processed_ids[-50:]
            downloaded_files.append(downloaded_file)
            
    # 4. Save state
    if downloaded_files:
        state[channel_url] = processed_ids
        save_state(state)
        
        # 5. Print each file path to stdout for orchestrator
        for df in downloaded_files:
            print(df)
        
    return downloaded_files

if __name__ == "__main__":
    main()
