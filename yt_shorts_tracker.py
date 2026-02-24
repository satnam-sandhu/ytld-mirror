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

def get_canonical_url(channel_url):
    """
    Resolves the canonical channel ID URL.
    Does a two-step resolution:
    1. Get a single video ID from the channel.
    2. Get the channel_id from that video's metadata.
    """
    # Step 1: Get any video ID
    cmd1 = ["yt-dlp", "--get-id", "--playlist-items", "1", "--flat-playlist", channel_url]
    try:
        res1 = subprocess.run(cmd1, capture_output=True, text=True, check=True)
        video_id = res1.stdout.strip()
        if video_id:
            # Step 2: Get channel_id from that video
            video_url = f"https://www.youtube.com/shorts/{video_id}"
            cmd2 = ["yt-dlp", "--print", "channel_id", "--playlist-items", "0", video_url]
            res2 = subprocess.run(cmd2, capture_output=True, text=True, check=True)
            cid = res2.stdout.strip()
            if cid and cid != "NA":
                canonical = f"https://www.youtube.com/channel/{cid}"
                sys.stderr.write(f"Resolved canonical URL: {canonical}\n")
                return canonical
    except subprocess.CalledProcessError:
        pass
    
    sys.stderr.write(f"Falling back to original URL: {channel_url}\n")
    return channel_url

def get_latest_short_id(channel_url):
    """
    Uses yt-dlp to get the ID of the single latest short.
    """
    # Use the /shorts tab of the canonical channel URL for stability
    canonical_base = get_canonical_url(channel_url)
    shorts_url = canonical_base.rstrip("/") + "/shorts"
    
    sys.stderr.write(f"Checking for latest short on: {shorts_url}\n")
    
    cmd = [
        "yt-dlp",
        "--get-id",
        "--playlist-end", "1", # Only the #1 latest
        "--flat-playlist",
        shorts_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        video_id = result.stdout.strip()
        return video_id
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error fetching channel data: {e.stderr}\n")
        return None

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
    
    # 1. Get the latest short ID
    latest_id = get_latest_short_id(channel_url)
    
    if not latest_id:
        sys.stderr.write(f"No shorts found on {channel_url}.\n")
        return None

    # 2. Load state
    state = load_state()
    saved_id = state.get(channel_url)
    
    # Check if saved_id is a list (from previous version) and convert to string
    if isinstance(saved_id, list):
        saved_id = saved_id[-1] if saved_id else None
            
    # 3. Compare and act
    if latest_id == saved_id:
        sys.stderr.write(f"No new shorts found for {channel_url}. (Current ID: {latest_id})\n")
        return None
    
    sys.stderr.write(f"New short detected: {latest_id} (Old: {saved_id})\n")
    
    # 4. Download
    downloaded_file = download_short(latest_id)
    if downloaded_file:
        # 5. Save state (as single string)
        state[channel_url] = latest_id
        save_state(state)
        
        # 6. Print file path to stdout for orchestrator
        print(downloaded_file)
        return downloaded_file
        
    return None

if __name__ == "__main__":
    main()
