#!/bin/bash

if ! command -v git &> /dev/null; then
  echo "git is not installed, attempting to install with apt."
  sudo apt install git
fi

if ! command -v python3.11 &> /dev/null; then
  echo "python 3.11 is not installed, please install it!"
  exit -1
fi

echo "Checking if pip is installed..."
python3.11 -m pip --version > /dev/null
if [ $? -ne 0 ]; then
  echo "python3.11 pip is not installed, attempting to install with ensurepip."
  python3.11 -m ensurepip
  if [ $? -ne 0 ]; then
    echo "pip was unable to be installed."
    exit -2
  fi
fi

echo "Checking if venv is installed..."
python3.11 -m venv -h > /dev/null
if [ $? -ne 0 ]; then
  echo "python3.11 venv is not installed, please install it!"
  exit -3
fi

echo "Cloning the repository..."
git clone https://github.com/SkyTheCodeMaster/status-monitor.git /tmp/status-monitor

echo "Copying client files to ./statuscd/"
mkdir ./statuscd/
cp -r /tmp/status-monitor/tools/client-daemon/* ./statuscd/

cwd=$(pwd)
cd ./statuscd/

echo "Ensuring execute permissions..."
chmod +x install.sh run.sh update.sh

echo "Creating python virtual environment under ./statuscd/venv/"
python3.11 -m venv venv

echo "Activating virtual environment"
source venv/bin/activate

echo "Installing pip dependencies..."
python3.11 -m pip install -r requirements.txt

echo "Creating config file"
echo "MACHINE_NAME = \"MACHINE NAME\"" > config.py
echo "SERVER_URL = \"http://SERVER URL/api/ws/start/\"" >> config.py

echo "Creating service file"
echo "[Unit]" > statuscd.service
echo "Description=Status Monitor Client Daemon" >> statuscd.service
echo "After=network.target" >> statuscd.service
echo -e "StartLimitIntervalSec=0\n" >> statuscd.service
echo "[Service]" >> statuscd.service
echo "Type=simple" >> statuscd.service
echo "Restart=always" >> statuscd.service
echo "RestartSec=1" >> statuscd.service
echo "WorkingDirectory=$(pwd)" >> statuscd.service
current_user="$(whoami 2>&1)"
echo "User=$current_user" >> statuscd.service
echo -e "ExecStart=$(pwd)/run.sh\n" >> statuscd.service
echo "[Install]" >> statuscd.service >> statuscd.service
echo "WantedBy=multi-user.target" >> statuscd.service

echo "Attempting to link service file"
sudo systemctl link $(pwd)/statuscd.service
echo "Attempting to enable service file"
sudo systemctl enable statuscd
echo "Starting service"
sudo systemctl start statuscd

echo "Cleaning up..."
rm -rf /tmp/status-monitor
cd $cwd

echo "All done!"
systemctl status statuscd