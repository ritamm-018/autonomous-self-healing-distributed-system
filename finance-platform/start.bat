@echo off
echo Starting Backend (Node.js Simulator)...
start cmd /k "cd backend && npm start"

echo Starting Frontend (React UI)...
start cmd /k "cd frontend && npm run dev"

echo Both services started.
