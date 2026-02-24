#!/bin/bash

echo "Listing all tracked YouTube channels in crontab:"
echo "------------------------------------------------"

crontab -l 2>/dev/null | grep "orchestrator.py" | while read -r line; do
    # Extract the URL which is the last argument
    URL=$(echo "$line" | grep -o 'https://[^"]*')
    if [ ! -z "$URL" ]; then
        echo "- $URL"
    fi
done

if [ $(crontab -l 2>/dev/null | grep -c "orchestrator.py") -eq 0 ]; then
    echo "No channels are currently being tracked."
fi
