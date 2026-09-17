#!/usr/bin/env bash
set -e

echo "Running NumberGuard Test Suite..."

# Backend Pytest Suite
./backend/.venv/bin/pytest backend/tests -v

echo "Testing Frontend Production Build..."
cd frontend && npm run build

echo "=== All Tests and Builds Passed Successfully ==="
