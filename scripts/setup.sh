#!/usr/bin/env bash
set -e

echo "=== NumberGuard Initial Environment Setup ==="

# Backend setup
echo "1. Setting up Python virtual environment..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Frontend setup
echo "2. Installing Frontend Node dependencies..."
cd ../frontend
npm install

# Database setup
echo "3. Seeding Initial Database..."
cd ..
./backend/.venv/bin/python database/seed.py

echo "=== NumberGuard Setup Completed Successfully ==="
echo "To start development servers: ./scripts/run_dev.sh"
