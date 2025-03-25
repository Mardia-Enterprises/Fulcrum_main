#!/bin/bash
# Start frontend
cd frontend && npm run dev &
# Start main API
cd ../backend/API && python run_api.py &
# Start projects API
cd ../API_projects && python run_api.py &
wait