#!/usr/bin/env bash

echo "Starting NumberGuard Backend & Frontend development servers..."

# Trap SIGINT to kill background jobs cleanly
trap 'kill $(jobs -p)' EXIT

# Start backend on 8000
./backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &

# Start frontend on 3000
cd frontend && npm run dev &

wait
