#!/bin/bash

# Get the directory where this script is located
SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( dirname "$SCRIPTS_DIR" )"
ORCHESTRATOR="$PROJECT_DIR/orchestrator.py"
# Try to find the conda python or use system python
PYTHON_CMD="$(which python)"

if [ -z "$1" ]; then
    echo "Usage: ./add_channel.sh <channel_url>"
    exit 1
fi

CHANNEL_URL=$1
CRON_JOB="*/30 * * * * $PYTHON_CMD $ORCHESTRATOR \"$CHANNEL_URL\" >> \"$PROJECT_DIR/cron_log.txt\" 2>&1"

# Check if it already exists
(crontab -l 2>/dev/null | grep -Fq "$CHANNEL_URL") && { echo "Channel already tracked."; exit 0; }

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Added cron job for: $CHANNEL_URL"
echo "It will run every 30 minutes."
