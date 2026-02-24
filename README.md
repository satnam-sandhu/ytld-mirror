# YouTube Shorts Automation (YTLD)

A powerful automation pipeline to track YouTube channels for new Shorts, download them, apply a custom watermark, and re-upload them to a target channel. This suite is designed for orchestration and scheduled via system cron jobs.

## 🚀 Features

- **Multi-Channel Tracking**: Tracks multiple channels independently using JSON state.
- **Smart Downloading**: Only downloads when a new video ID is detected.
- **Auto-Watermarking**: Adds a centered "hecker boizz" watermark with 50% opacity using FFmpeg.
- **YouTube Uploading**: Handles OAuth2 and resumable uploads via YouTube Data API v3.
- **Cron Orchestration**: Manage automated tasks with simple bash scripts.

## 📋 Prerequisites

- **Python**: 3.10 or higher.
- **Conda**: Recommended for environment management.
- **FFmpeg**: Required for watermarking.
- **Google Cloud Credentials**: `client_secret.json` with YouTube Data API v3 access.

## 🛠️ Getting Started

### 1. Environment Setup
```bash
# Create and activate environment
conda create -y -n yt_shorts_downloader python=3.10
conda activate yt_shorts_downloader

# Install dependencies
pip install -r requirements.txt
```

### 2. YouTube API Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **YouTube Data API v3**.
3. Create OAuth 2.0 Client IDs and download the JSON file.
4. Rename it to `client_secret.json` and place it in the root of this project.

## ⚙️ Usage

### Automated Tracking (Cron)
Manage your automation using the provided bash scripts:

- **Add a channel**:
  ```bash
  ./scripts/add_channel.sh "https://www.youtube.com/@ChannelName"
  ```
  *(Default: checks every hour)*

- **List active channels**:
  ```bash
  ./scripts/list_channels.sh
  ```

- **Remove a channel**:
  ```bash
  ./scripts/remove_channel.sh "https://www.youtube.com/@ChannelName"
  ```

### Manual Orchestration
Run the entire pipeline for a specific channel manually:
```bash
python orchestrator.py "https://www.youtube.com/@ChannelName"
```

## 🏗️ Project Structure

- `yt_shorts_tracker.py`: Metadata check and downloading logic.
- `watermark_video.py`: Video processing using FFmpeg.
- `upload_video.py`: YouTube API integration.
- `orchestrator.py`: Coordination of the full pipeline.
- `scripts/`: Cron management utilities.
- `processed_shorts.json`: Multi-channel state tracking.
