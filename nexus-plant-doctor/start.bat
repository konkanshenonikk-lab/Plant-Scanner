@echo off
title Nexus Plant Doctor
cd /d "%~dp0"

if not exist "frontend\dist\index.html" (
  echo Building frontend for the first time...
  pushd frontend
  call npm install --no-fund --no-audit
  call npm run build
  popd
)

echo Starting API + UI at http://localhost:8000
cd backend
python main.py
pause
