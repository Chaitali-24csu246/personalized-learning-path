@echo off
cd /d "%~dp0"
py -3 start.py
if errorlevel 1 (
  echo Install Python 3 from python.org or run python start.py from this folder.
  pause
)
