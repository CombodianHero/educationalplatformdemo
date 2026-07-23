#!/bin/bash

# Start backend in background
cd /app
python main.py &
BACKEND_PID=$!

# Start frontend
cd /app/frontend
npx next start -p 3000 &
FRONTEND_PID=$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
