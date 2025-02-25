#!/bin/bash

# If "done.txt" exists, exit immediately.
if [ -f done.txt ]; then
  echo "All tasks complete. Exiting."
  exit 0
fi

while true; do
  echo "Starting puppet6.js..."
  node puppet6.js
  # Check if the script has signaled that it's finished.
  if [ -f done.txt ]; then
    echo "All tasks complete. Exiting."
    exit 0
  fi
  echo "JS script exited. Waiting 10 seconds before restarting..."
  sleep 10
done