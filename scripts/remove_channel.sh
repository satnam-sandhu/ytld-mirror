#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./remove_channel.sh <channel_url>"
    exit 1
fi

CHANNEL_URL=$1

# Remove from crontab
(crontab -l 2>/dev/null | grep -vF "$CHANNEL_URL") | crontab -

echo "Removed cron job for: $CHANNEL_URL (if it existed)"
