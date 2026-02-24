import os
import sys
import subprocess
import json

# Determine the absolute directory of the script for cron compatibility
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "processed_shorts.json")
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "downloads")

def get_latest_short_id(channel_url):
    """
    Uses yt-dlp to get the ID of the latest short from the channel.
    """
    sys.stderr.write(f"Checking for latest shorts on: {channel_url}\n")
    
    # We append /shorts to the channel URL to target specifically the shorts tab
    shorts_url = channel_url.rstrip("/") + "/shorts"
    
    cmd = [
        "yt-dlp",
        "--get-id",
        "--playlist-items", "1",
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
            "-o", target_file,
            url
        ]
        subprocess.run(download_cmd, check=True)
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
        
    channel_url = sys.argv[1].rstrip("/")
    
    # 1. Get the latest short ID from the channel
    latest_id = get_latest_short_id(channel_url)
    
    if not latest_id:
        sys.stderr.write("Could not find any shorts on this channel.\n")
        return None

    # 2. Check the saved ID in the tracking file (JSON format)
    state = load_state()
    saved_id = state.get(channel_url)
            
    # 3. Compare and act
    if latest_id == saved_id:
        sys.stderr.write(f"No new shorts found for {channel_url}. (Current ID: {latest_id})\n")
        return None
    else:
        sys.stderr.write(f"New short detected on {channel_url}! (New ID: {latest_id}, Old ID: {saved_id})\n")
        
        # 4. Download the new short
        downloaded_file = download_short(latest_id)
        if downloaded_file:
            # 5. Update the tracking state
            state[channel_url] = latest_id
            save_state(state)
            sys.stderr.write(f"Updated {STATE_FILE} with new ID for {channel_url}.\n")
            
            # Print to stdout for the orchestrator to capture
            print(downloaded_file)
            return downloaded_file
    
    return None

if __name__ == "__main__":
    main()
