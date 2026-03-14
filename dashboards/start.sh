#!/bin/bash
cd "$(dirname "$0")"
echo "Installing dependencies..."
pip install -r requirements.txt -q
echo "Starting Dashboard Server at http://localhost:8500"
python3 server.py
