#!/bin/bash

echo "Running updater..."

echo "Moving existing files into archive directory"
if [ -d "$(pwd)/old" ]; then
  rm -rf "$(pwd)/old"
fi

mkdir "$(pwd)/old"

echo "Moving files"
mv statuscd.py "$(pwd)/old"
mv plugins.py "$(pwd)/old"
mv requirements.txt "$(pwd)/old"
mv watchdog.py "$(pwd)/old"

if [ -d "/tmp/status-monitor/" ]; then
  rm -rf /tmp/status-monitor/
fi
echo "Cloning the repository..."
git clone https://github.com/SkyTheCodeMaster/status-monitor.git /tmp/status-monitor

echo "Deleting old files"
rm statuscd.py plugins.py requirements.txt

echo "Copying new files..."
cp /tmp/status-monitor/tools/client-daemon/requirements.txt .
cp /tmp/status-monitor/tools/client-daemon/plugins.py .
cp /tmp/status-monitor/tools/client-daemon/statuscd.py .
cp /tmp/status-monitor/tools/client-daemon/watchdog.py .

echo "Removing old venv"
if [ -d "$(pwd)/venv" ]; then
  rm -rf "$(pwd)/venv"
fi

echo "Creating new venv"
python3.11 -m venv venv
source venv/bin/activate
python3.11 -m pip install -r requirements.txt

echo "All done!"
exit