#!/usr/bin/env bash
set -e

echo "Populating NumberGuard database with realistic records..."
./backend/.venv/bin/python database/seed.py
echo "Seeding completed."
