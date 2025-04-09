#!/bin/bash
set -e

# Create directories if they don't exist
mkdir -p /app/staticfiles
mkdir -p /app/media
mkdir -p /app/logs

# Change ownership to appuser if running as root
if [ "$(id -u)" = "0" ]; then
  echo "Setting correct permissions..."
  chown -R appuser:appuser /app/staticfiles
  chown -R appuser:appuser /app/media
  chown -R appuser:appuser /app/logs

  # Execute command as appuser
  echo "Running command as appuser..."
  exec gosu appuser "$@"
else
  # Run directly if already running as appuser
  exec "$@"
fi